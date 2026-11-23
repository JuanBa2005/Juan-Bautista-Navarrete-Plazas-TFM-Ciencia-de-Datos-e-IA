"""EDA reproducible del Gold de TallerPredict (Entrega 03, paso 1).

Ejecutar desde la raíz del repositorio: python scripts/etapa_3/analisis_exploratorio_gold.py

Requisitos: pandas, numpy, matplotlib.
"""
from pathlib import Path
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'datos' / 'processed' / 'gold_consumo_mensual_repuestos.csv'
OUT = ROOT / 'resultados' / 'ml' / 'eda'
TARGET = 'target_next_month_units'
REQUIRED = {'part_id', 'part_code', 'part_name', 'unit', 'month_date', 'calendar_year',
            'calendar_month', 'lag_1_units', 'lag_2_units', 'lag_3_units',
            'rolling_3_units', TARGET}


def main():
    if not SOURCE.is_file():
        sys.exit(f'ERROR: Gold no encontrado en {SOURCE}. Ejecuta desde el repositorio que contiene datos/processed/.')
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SOURCE, parse_dates=['month_date'])
    missing = REQUIRED - set(df.columns)
    if missing:
        sys.exit(f'ERROR: faltan columnas en Gold: {sorted(missing)}')
    df = df.sort_values(['month_date', 'part_id']).reset_index(drop=True)
    df['target_month'] = df['month_date'] + pd.offsets.MonthBegin(1)
    duplicates = int(df.duplicated(['part_id', 'month_date']).sum())
    nulls = df.isna().sum().to_dict()
    negatives = {c: int((df[c] < 0).sum()) for c in ['lag_1_units','lag_2_units','lag_3_units', TARGET]}
    months = pd.date_range(df.month_date.min(), df.month_date.max(), freq='MS')
    actual_pairs = df[['part_id', 'month_date']].drop_duplicates().shape[0]
    expected_pairs = df.part_id.nunique() * len(months)
    invalid_month = int(((df.month_date.dt.year != df.calendar_year) |
                         (df.month_date.dt.month != df.calendar_month)).sum())
    rolling_diff = (df['rolling_3_units'] - df[['lag_1_units','lag_2_units','lag_3_units']].mean(axis=1)).abs()
    stats = {
        'filas': int(len(df)), 'columnas_gold': int(df.shape[1]-1),
        'repuestos': int(df.part_id.nunique()), 'meses_referencia': int(df.month_date.nunique()),
        'fecha_inicial_referencia': df.month_date.min().strftime('%Y-%m'),
        'fecha_final_referencia': df.month_date.max().strftime('%Y-%m'),
        'fechas_objetivo': [df.target_month.min().strftime('%Y-%m'), df.target_month.max().strftime('%Y-%m')],
        'nulos_por_columna': {k: int(v) for k,v in nulls.items()},
        'duplicados_repuesto_mes': duplicates, 'pares_repuesto_mes_ausentes': int(expected_pairs-actual_pairs),
        'fechas_calendario_inconsistentes': invalid_month,
        'valores_negativos': negatives, 'desviaciones_media_movil_mayores_0_0001': int((rolling_diff > .0001).sum()),
        'porcentaje_objetivo_cero': round(100 * df[TARGET].eq(0).mean(), 2),
        'media_objetivo': round(float(df[TARGET].mean()), 4),
        'mediana_objetivo': round(float(df[TARGET].median()), 4),
        'maximo_objetivo': float(df[TARGET].max()),
        'unidades': {str(k): int(v) for k,v in df.unit.value_counts().items()},
    }
    (OUT / 'resumen_eda.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')

    # Estadísticas POR REPUESTO: no sumar consumos de unidades heterogéneas.
    per_part = df.groupby(['part_id', 'part_code', 'part_name', 'unit'], as_index=False).agg(
        meses=('month_date','size'), consumo_medio_mensual=(TARGET,'mean'),
        consumo_maximo_mensual=(TARGET,'max'), meses_sin_consumo=(TARGET, lambda s: int(s.eq(0).sum())),
        desviacion_consumo=(TARGET,'std'))
    per_part['porcentaje_meses_sin_consumo'] = (100*per_part.meses_sin_consumo/per_part.meses).round(2)
    per_part.to_csv(OUT/'resumen_por_repuesto.csv', index=False, encoding='utf-8-sig')
    by_unit = df.groupby('unit',as_index=False).agg(
        registros=(TARGET,'size'), consumo_medio=(TARGET,'mean'),
        porcentaje_ceros=(TARGET, lambda s: round(100*s.eq(0).mean(),2)))
    by_unit.to_csv(OUT/'resumen_por_unidad.csv',index=False,encoding='utf-8-sig')

    # Gráfico 1: ceros vs consumos positivos.
    fig, ax = plt.subplots(figsize=(7,4.5))
    counts = [int(df[TARGET].eq(0).sum()),int(df[TARGET].gt(0).sum())]
    ax.bar(['Sin consumo registrado', 'Consumo positivo'], counts)
    ax.set(ylabel='Número de registros',title='Distribución de consumos objetivo: cero vs positivo')
    for i, v in enumerate(counts): ax.text(i,v+12,str(v),ha='center')
    fig.tight_layout();fig.savefig(OUT/'01_ceros_vs_positivos.png',dpi=150);plt.close(fig)

    # Gráfico 2: histograma solo de consumos positivos; no mezcla totales de unidades.
    fig,ax=plt.subplots(figsize=(8,4.5))
    for unit, group in df[df[TARGET]>0].groupby('unit'):
        ax.hist(group[TARGET],bins=20,alpha=.35,label=unit)
    ax.set(xlabel='Cantidad en la unidad indicada por la leyenda',ylabel='Registros',
           title='Distribución de consumos positivos por tipo de unidad')
    ax.legend(title='Unidad');fig.tight_layout()
    fig.savefig(OUT/'02_distribucion_positivos.png',dpi=150);plt.close(fig)

    # Gráfico 3: serie en una sola unidad (ud); evita suma de kg/litros/unidades.
    monthly = df[df.unit=='ud'].groupby('target_month')[TARGET].sum()
    fig, ax=plt.subplots(figsize=(10,4))
    ax.plot(monthly.index,monthly.values,marker='o',markersize=3)
    ax.set(title='Consumo mensual registrado de repuestos medidos en ud',
           xlabel='Mes de consumo (mes objetivo)',ylabel='Cantidad total (ud)')
    fig.autofmt_xdate();fig.tight_layout()
    fig.savefig(OUT/'03_evolucion_mensual_ud.png',dpi=150);plt.close(fig)
    monthly.rename('total_ud').to_csv(OUT/'serie_mensual_ud.csv',encoding='utf-8-sig')

    # Gráfico 4: repuestos de tipo ud con mayor media mensual.
    top=per_part[per_part.unit=='ud'].nlargest(12,'consumo_medio_mensual').sort_values('consumo_medio_mensual')
    fig,ax=plt.subplots(figsize=(10,6))
    ax.barh(top.part_name,top.consumo_medio_mensual)
    ax.set(xlabel='Consumo medio por mes (ud)',title='12 repuestos (ud) con mayor consumo medio')
    fig.tight_layout();fig.savefig(OUT/'04_top_repuestos_ud.png',dpi=150);plt.close(fig)

    # Gráfico 5: variabilidad e intermitencia por repuesto.
    fig,ax=plt.subplots(figsize=(8,4.5))
    ax.hist(per_part.porcentaje_meses_sin_consumo,bins=10)
    ax.set(xlabel='Porcentaje de meses con consumo cero por repuesto',
           ylabel='Número de repuestos',title='Intermitencia del consumo')
    fig.tight_layout();fig.savefig(OUT/'05_intermitencia.png',dpi=150);plt.close(fig)

    print('\n=== TALLERPREDICT | EDA GOLD ===')
    print(f"Registros: {stats['filas']} | Repuestos: {stats['repuestos']} | Meses: {stats['meses_referencia']}")
    print(f"Periodo referencia: {stats['fecha_inicial_referencia']} a {stats['fecha_final_referencia']}")
    print(f"Periodo objetivo: {' a '.join(stats['fechas_objetivo'])}")
    print(f"Nulos: {sum(nulls.values())} | Duplicados: {duplicates} | Pares faltantes: {expected_pairs-actual_pairs}")
    print(f"Porcentaje de objetivo cero: {stats['porcentaje_objetivo_cero']}%")
    print(f"Media: {stats['media_objetivo']} | Mediana: {stats['mediana_objetivo']} | Máximo: {stats['maximo_objetivo']}")
    print('Unidades:', stats['unidades'])
    print(f'Archivos guardados en: {OUT}')
    print('NOTA: las estadísticas de la variable objetivo incluyen periodos posteriores a cada mes de referencia.')
    print('      Se usan para EDA, no para entrenar ni seleccionar un modelo sobre el conjunto de prueba.')

if __name__=='__main__':
    main()
