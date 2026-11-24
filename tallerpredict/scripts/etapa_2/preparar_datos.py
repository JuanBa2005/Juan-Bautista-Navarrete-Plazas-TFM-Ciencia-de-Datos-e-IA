#!/usr/bin/env python3
"""Entrega 02: procesamiento determinista de datos CSV locales a Silver y Gold.
Ejecutar desde cualquier directorio: python scripts/preparar_datos.py
Requiere pandas (ver requirements-data.txt). No entrena modelos.
"""
from pathlib import Path
import json
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
RAW = BASE / 'datos'
OUT = RAW / 'processed'
FILES = ('vehicles', 'repair_types', 'parts', 'work_orders', 'repair_events', 'part_usage', 'inventory_movements')
DATES = {'work_orders': ('entry_at', 'exit_at'), 'repair_events': ('performed_at',), 'inventory_movements': ('movement_at',)}
REFERENCES = [
    ('work_orders', 'vehicle_id', 'vehicles'),
    ('repair_events', 'order_id', 'work_orders'),
    ('repair_events', 'repair_type_id', 'repair_types'),
    ('part_usage', 'repair_event_id', 'repair_events'),
    ('part_usage', 'part_id', 'parts'),
    ('inventory_movements', 'part_id', 'parts'),
    ('inventory_movements', 'repair_event_id', 'repair_events'),
]


def assert_ok(condition, description):
    if not condition:
        raise ValueError(description)


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    data = {}
    report = {'fuente': 'CSV adjuntos en datos/ (origen primario externo sin acreditar)', 'bronze': {}, 'silver': {}, 'gold': {}}
    for name in FILES:
        source = RAW / f'{name}.csv'
        assert_ok(source.exists(), f'Falta CSV de origen: {source}')
        df = pd.read_csv(source, low_memory=False)
        report['bronze'][name] = {'filas': len(df), 'columnas': len(df.columns)}
        assert_ok('id' in df.columns, f'Sin identificador en {name}')
        dupe_ids = int(df.duplicated('id').sum())
        assert_ok(dupe_ids == 0, f'Identificadores duplicados en {name}: {dupe_ids}')
        for col in DATES.get(name, ()):
            df[col] = pd.to_datetime(df[col], errors='coerce')
            assert_ok(not df[col].isna().any() or (name == 'work_orders' and col == 'exit_at'), f'Fecha inválida en {name}.{col}')
        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].str.strip()
        data[name] = df
        report['silver'][name] = {'filas': len(df), 'ids_duplicados': dupe_ids, 'nulos_por_campo': {k: int(v) for k, v in df.isna().sum().items() if v > 0}}
    for child, fk, parent in REFERENCES:
        unknown = set(data[child][fk].dropna()) - set(data[parent]['id'])
        assert_ok(not unknown, f'Referencia no encontrada: {child}.{fk} → {parent}: {len(unknown)}')
    assert_ok((data['part_usage']['quantity'] > 0).all(), 'Consumo de piezas no positivo')
    assert_ok((data['parts']['unit_cost'] >= 0).all(), 'Coste negativo')
    assert_ok((data['parts']['supplier_lead_days'] >= 0).all(), 'Plazo de suministro negativo')
    orders = data['work_orders']
    assert_ok(((orders.exit_at.isna()) | (orders.exit_at >= orders.entry_at)).all(), 'Orden con salida anterior a entrada')
    for name, df in data.items():
        df.to_csv(OUT / f'silver_{name}.csv', index=False, date_format='%Y-%m-%d %H:%M:%S')

    # La demanda observada es el número de unidades consumidas por reparación:
    # no se utiliza quantity_delta para evitar mezclar compras/ajustes con consumo.
    usage = data['part_usage'][['repair_event_id', 'part_id', 'quantity']].merge(
        data['repair_events'][['id', 'performed_at']],
        how='left', left_on='repair_event_id', right_on='id', validate='many_to_one'
    )
    usage['month'] = usage['performed_at'].dt.to_period('M')
    monthly = usage.groupby(['part_id', 'month'], as_index=False)['quantity'].sum()
    first = usage['month'].min()
    last = usage['month'].max()
    assert_ok(pd.notna(first) and first < last, 'Histórico insuficiente')
    # Meses ausentes se interpretan como cero consumos REGISTRADOS, no demanda real nula.
    months = pd.period_range(first, last, freq='M')
    grid = pd.MultiIndex.from_product([sorted(data['parts'].id), months], names=['part_id', 'month'])
    series = monthly.set_index(['part_id', 'month'])['quantity'].reindex(grid, fill_value=0).rename('consumption_units').reset_index()
    parts = data['parts'][['id', 'part_code', 'name', 'unit', 'unit_cost', 'supplier_lead_days']].rename(columns={'id': 'part_id', 'name': 'part_name'})
    series = series.merge(parts, on='part_id', validate='many_to_one')
    series = series.sort_values(['part_id', 'month']).reset_index(drop=True)
    grouped = series.groupby('part_id', sort=False)['consumption_units']
    series['lag_1_units'] = grouped.shift(0)
    series['lag_2_units'] = grouped.shift(1)
    series['lag_3_units'] = grouped.shift(2)
    series['rolling_3_units'] = grouped.transform(lambda x: x.rolling(3, min_periods=3).mean())
    # La etiqueta es el consumo del mes SIGUIENTE. La predicción se realiza
    # al CIERRE del mes de referencia, cuando su consumo ya se conoce.
    # Etiqueta disponible solo si el mes siguiente está incluido en el histórico.
    series['target_next_month_units'] = grouped.shift(-1)
    series['month_date'] = series['month'].dt.to_timestamp().dt.strftime('%Y-%m-%d')
    series['calendar_month'] = series['month'].dt.month
    series['calendar_year'] = series['month'].dt.year
    gold = series.dropna(subset=['lag_1_units', 'lag_2_units', 'lag_3_units', 'rolling_3_units', 'target_next_month_units']).copy()
    gold = gold[['part_id', 'part_code', 'part_name', 'unit', 'month_date', 'calendar_year', 'calendar_month', 'unit_cost', 'supplier_lead_days', 'lag_1_units', 'lag_2_units', 'lag_3_units', 'rolling_3_units', 'target_next_month_units']]
    assert_ok(not gold.isna().any().any(), 'Nulos inesperados en Gold')
    assert_ok(gold.duplicated(['part_id', 'month_date']).sum() == 0, 'Duplicados en Gold')
    gold.to_csv(OUT / 'gold_consumo_mensual_repuestos.csv', index=False, float_format='%.4f')
    report['gold'] = {'filas': len(gold), 'columnas': list(gold.columns), 'piezas': int(gold.part_id.nunique()), 'primer_mes_referencia': str(gold.month_date.min()), 'ultimo_mes_referencia': str(gold.month_date.max()), 'horizonte_objetivo': 'un mes después del mes de referencia', 'rango_observado': [str(first), str(last)], 'unidades_objetivo_totales': float(gold.target_next_month_units.sum()), 'nulos': int(gold.isna().sum().sum())}
    (OUT / 'reporte_calidad.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"OK: Bronze 7 CSV; Silver 7 CSV; Gold {len(gold)} filas x {len(gold.columns)} columnas, {gold.part_id.nunique()} repuestos")
    print(f"Referencia Gold: {gold.month_date.min()} -> {gold.month_date.max()}")

if __name__ == '__main__':
    run()
