"""TallerPredict - Paso 2: auditoría de variables y partición temporal (sin entrenamiento).

Ejecutar desde la raíz del repositorio: python scripts/etapa_3/preparar_experimento_ml.py

Requisitos: pandas, numpy.
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / 'datos' / 'processed' / 'gold_consumo_mensual_repuestos.csv'
OUT = ROOT / 'resultados' / 'ml' / 'diseno_experimento'
TARGET = 'target_next_month_units'
FEATURES = ['part_id', 'lag_1_units', 'lag_2_units', 'lag_3_units', 'rolling_3_units', 'target_calendar_month']
TRAIN_END = pd.Timestamp('2023-05-01')
VAL_END = pd.Timestamp('2023-08-01')


def run():
    if not GOLD.is_file():
        raise FileNotFoundError(f'No se ha encontrado el Gold: {GOLD}')
    df = pd.read_csv(GOLD, parse_dates=['month_date'])
    required = set(FEATURES) - {'target_calendar_month'} | {TARGET, 'month_date', 'unit', 'part_code'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'Columnas ausentes: {sorted(missing)}')
    if df[list(required)].isna().any().any():
        raise ValueError('Hay valores nulos en columnas esenciales')
    if df.duplicated(['part_id', 'month_date']).any():
        raise ValueError('Hay duplicados por repuesto-mes')
    if (df[[TARGET, 'lag_1_units', 'lag_2_units', 'lag_3_units', 'rolling_3_units']] < 0).any().any():
        raise ValueError('Se detectaron consumos negativos')
    df['target_month_date'] = df['month_date'] + pd.offsets.MonthBegin(1)
    df['target_calendar_month'] = df['target_month_date'].dt.month
    if not df.groupby('part_id')['unit'].nunique().eq(1).all():
        raise ValueError('Una misma pieza aparece con unidades inconsistentes')
    df['split'] = 'test'
    df.loc[df['month_date'] <= TRAIN_END, 'split'] = 'train'
    df.loc[(df['month_date'] > TRAIN_END) & (df['month_date'] <= VAL_END), 'split'] = 'validation'
    if df['split'].value_counts().reindex(['train','validation','test'],fill_value=0).eq(0).any():
        raise ValueError('Alguna partición está vacía')
    # Dejar test sin evaluar: se audita solamente el tamaño y el rango temporal.
    summary = []
    for split in ['train', 'validation', 'test']:
        g = df.loc[df.split == split]
        summary.append({
            'particion': split, 'filas': int(len(g)), 'repuestos': int(g.part_id.nunique()),
            'meses_referencia': int(g.month_date.nunique()),
            'inicio_referencia': g.month_date.min().strftime('%Y-%m'),
            'fin_referencia': g.month_date.max().strftime('%Y-%m'),
            'inicio_objetivo': g.target_month_date.min().strftime('%Y-%m'),
            'fin_objetivo': g.target_month_date.max().strftime('%Y-%m'),
            'porcentaje_objetivos_cero': None if split == 'test' else round(float(g[TARGET].eq(0).mean()*100),2)
        })
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary).to_csv(OUT / 'particiones_temporales.csv', index=False)
    df[['part_id', 'part_code', 'unit', 'month_date', 'target_month_date', 'target_calendar_month', 'split']].to_csv(OUT / 'auditoria_particiones.csv', index=False, date_format='%Y-%m-%d')
    schema = {'objetivo': TARGET, 'variables_entrada': FEATURES, 'variable_categorica': ['part_id'],
              'variables_numericas': [x for x in FEATURES if x != 'part_id'],
              'particiones': summary,
              'nota': 'No entrenar ni ajustar transformaciones con test. Consumos del mes de referencia conocidos al cierre.'}
    (OUT / 'configuracion_experimento.json').write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding='utf-8')
    print('=== TALLERPREDICT | PASO 2: DISENO EXPERIMENTO ===')
    print('Objetivo:', TARGET)
    print('Entradas:', ', '.join(FEATURES))
    print(pd.DataFrame(summary).to_string(index=False))
    print('Archivos guardados en:', OUT)


if __name__ == '__main__':
    run()
