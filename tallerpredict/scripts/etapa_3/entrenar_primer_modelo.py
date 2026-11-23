#!/usr/bin/env python3
"""TallerPredict | Paso 4: primer modelo de Machine Learning (Ridge).

Se ejecuta desde la raíz del repositorio:
    python scripts/etapa_3/entrenar_primer_modelo.py

Requisitos: pandas, numpy, matplotlib, scikit-learn.
No se entrena ni evalúa con etiquetas del conjunto TEST.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / 'datos' / 'processed' / 'gold_consumo_mensual_repuestos.csv'
OUT = ROOT / 'resultados' / 'ml' / 'primer_modelo'
TARGET = 'target_next_month_units'
TRAIN_END = pd.Timestamp('2023-05-01')
VAL_END = pd.Timestamp('2023-08-01')
FEATURES = ['part_id', 'lag_1_units', 'lag_2_units', 'lag_3_units',
            'rolling_3_units', 'target_calendar_month']
NUMERIC = [f for f in FEATURES if f != 'part_id']
BASELINES = {'siempre_cero': None, 'ultimo_mes': 'lag_1_units',
             'media_tres_meses': 'rolling_3_units'}
ALPHA = 10.0  # Parámetro fijado de antemano. No se optimiza con TEST.


def evaluate(group: pd.DataFrame) -> dict:
    y = group[TARGET].to_numpy(dtype=float)
    pred = group['prediccion'].to_numpy(dtype=float)
    err = pred - y
    positive = y > 0
    return {
        'n': int(len(group)),
        'mae_mixto_solo_diagnostico': float(np.mean(np.abs(err))),
        'rmse_mixto_solo_diagnostico': float(np.sqrt(np.mean(err**2))),
        'mae_escalado_macro_repuesto': float(group.groupby('part_id')['error_escalado'].mean().mean()),
        'mae_consumos_positivos_mixto_solo_diagnostico': (
            float(np.mean(np.abs(err[positive]))) if positive.any() else None),
        'fallos_cero_ante_consumo_positivo': int(np.count_nonzero(positive & (pred == 0))),
        'sesgo_mixto_solo_diagnostico': float(np.mean(err)),
    }


def main() -> None:
    if not GOLD.is_file():
        raise FileNotFoundError(f'No se ha encontrado el Gold: {GOLD}')
    df = pd.read_csv(GOLD, parse_dates=['month_date'])
    required = set(FEATURES) - {'target_calendar_month'} | {
        'month_date', TARGET, 'unit', 'part_code', 'part_name'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'Columnas ausentes: {sorted(missing)}')
    if df[list(required)].isna().any().any():
        raise ValueError('Nulos detectados en columnas esenciales')
    if df.duplicated(['part_id', 'month_date']).any():
        raise ValueError('Duplicados repuesto-mes detectados')
    units = ['lag_1_units', 'lag_2_units', 'lag_3_units', 'rolling_3_units', TARGET]
    if (df[units] < 0).any().any():
        raise ValueError('Hay consumos negativos')
    if not df.groupby('part_id')['unit'].nunique().eq(1).all():
        raise ValueError('Un repuesto tiene varias unidades de medida')

    df['target_calendar_month'] = (df['month_date'] + pd.offsets.MonthBegin(1)).dt.month
    # part_id es una categoría, no una variable numérica ordinal.
    df['part_id'] = df['part_id'].astype(str)
    train = df.loc[df['month_date'] <= TRAIN_END].copy()
    val = df.loc[(df['month_date'] > TRAIN_END) & (df['month_date'] <= VAL_END)].copy()
    n_test = int((df['month_date'] > VAL_END).sum())
    if train.empty or val.empty or n_test == 0:
        raise ValueError('Las particiones temporales no contienen datos')
    if train['month_date'].max() >= val['month_date'].min():
        raise ValueError('Train y validation no están ordenados cronológicamente')
    if not set(val.part_id).issubset(set(train.part_id)):
        raise ValueError('Hay repuestos en validación que no aparecen en train')

    preprocessor = ColumnTransformer([
        ('repuesto', OneHotEncoder(handle_unknown='ignore'), ['part_id']),
        ('numericas', StandardScaler(), NUMERIC),
    ])
    model = Pipeline([
        ('preparacion', preprocessor),
        ('regresion', Ridge(alpha=ALPHA)),
    ])
    # FIT completo solamente sobre entrenamiento: OneHot, StandardScaler y Ridge.
    model.fit(train[FEATURES], train[TARGET])
    ridge_raw = model.predict(val[FEATURES])
    ridge_pred = np.maximum(ridge_raw, 0.0)  # Consumo negativo no es físicamente válido.

    scale = train.groupby('part_id')[TARGET].mean().clip(lower=1).rename('escala_train')
    val = val.merge(scale, on='part_id', validate='many_to_one', how='left')
    if val['escala_train'].isna().any():
        raise ValueError('Escalas de entrenamiento incompletas')

    outputs = []
    for name, col in BASELINES.items():
        p = np.zeros(len(val)) if col is None else val[col].to_numpy(dtype=float)
        outputs.append((name, np.maximum(p, 0)))
    outputs.append(('ridge', ridge_pred))

    predictions = []
    for name, p in outputs:
        g = val[['part_id', 'part_code', 'part_name', 'unit', 'month_date',
                 TARGET, 'escala_train']].copy()
        g['modelo'] = name
        g['prediccion'] = p
        g['error'] = g['prediccion'] - g[TARGET]
        g['error_absoluto'] = g['error'].abs()
        g['error_escalado'] = g['error_absoluto'] / g['escala_train']
        predictions.append(g)
    predictions = pd.concat(predictions, ignore_index=True)

    metricas = pd.DataFrame([
        {'modelo': name, **evaluate(g)} for name, g in predictions.groupby('modelo', sort=False)
    ])
    by_unit = pd.DataFrame([
        {'modelo': name, 'unidad': unit, 'n': int(len(g)),
         'mae': float(g['error_absoluto'].mean()),
         'mae_consumos_positivos': (
             float(g.loc[g[TARGET] > 0, 'error_absoluto'].mean())
             if (g[TARGET] > 0).any() else None)}
        for (name, unit), g in predictions.groupby(['modelo', 'unit'], sort=True)
    ])
    by_part = pd.DataFrame([
        {'modelo': name, 'part_id': part, 'part_code': g.part_code.iloc[0],
         'part_name': g.part_name.iloc[0], 'unidad': g.unit.iloc[0],
         'mae': float(g.error_absoluto.mean()),
         'mae_escalado': float(g.error_escalado.mean())}
        for (name, part), g in predictions.groupby(['modelo', 'part_id'], sort=True)
    ])
    errors = (predictions.loc[predictions.modelo.eq('ridge')]
              .sort_values('error_escalado', ascending=False).head(20).copy())

    OUT.mkdir(parents=True, exist_ok=True)
    metricas.round(6).to_csv(OUT / 'metricas_validacion_comparacion.csv', index=False)
    by_unit.round(6).to_csv(OUT / 'metricas_validacion_por_unidad.csv', index=False)
    by_part.round(6).to_csv(OUT / 'metricas_validacion_por_repuesto.csv', index=False)
    predictions.to_csv(OUT / 'predicciones_validacion_comparadas.csv', index=False)
    errors.to_csv(OUT / 'mayores_errores_ridge_validacion.csv', index=False)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    plot = metricas.sort_values('mae_escalado_macro_repuesto')
    ax.bar(plot.modelo, plot.mae_escalado_macro_repuesto)
    ax.set_title('TallerPredict - Ridge frente a baselines (validación)')
    ax.set_ylabel('MAE escalado por repuesto (menor es mejor)')
    fig.tight_layout()
    fig.savefig(OUT / '01_mae_escalado_modelos.png', dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    unit_plot = by_unit.pivot(index='unidad', columns='modelo', values='mae')
    unit_plot.plot(kind='bar', ax=ax)
    ax.set_title('MAE por unidad de medida (validación)')
    ax.set_ylabel('MAE en la unidad indicada')
    ax.tick_params(axis='x', rotation=0)
    fig.tight_layout()
    fig.savefig(OUT / '02_mae_por_unidad.png', dpi=150)
    plt.close(fig)

    metadata = {
        'modelo': 'Ridge con OneHotEncoder(part_id) y StandardScaler(variables numéricas)',
        'alpha': ALPHA, 'objetivo': TARGET, 'variables': FEATURES,
        'filas_entrenamiento': len(train), 'filas_validacion': len(val),
        'filas_test_reservadas': n_test,
        'fechas_referencia_train': [str(train.month_date.min().date()), str(train.month_date.max().date())],
        'fechas_referencia_validation': [str(val.month_date.min().date()), str(val.month_date.max().date())],
        'seleccion_modelo': 'No se ha seleccionado un modelo definitivo. Comparación en validación.',
        'advertencias': [
            'No comparar MAE/RMSE mezclados como magnitudes físicas entre unidades.',
            'El MAE escalado usa max(media objetivo por repuesto en train, 1).',
            'Las métricas en meses positivos son condicionadas al valor real: no son una métrica operativa única.',
            'No se han utilizado etiquetas del conjunto test.',
            'Un primer experimento de regresión no garantiza utilidad para el MVP.',
        ],
    }
    (OUT / 'configuracion_primer_modelo.json').write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\n=== TALLERPREDICT | PASO 4: PRIMER MODELO RIDGE ===')
    print(f'Entrenamiento: {len(train)} | Validacion: {len(val)} | Test reservado: {n_test}')
    print('\nMETRICAS EN VALIDACION (errores mixtos SOLO orientativos):')
    print(metricas.round(4).to_string(index=False))
    print('\nMAE POR UNIDAD (sin mezclar magnitudes):')
    print(unit_plot.round(4).to_string())
    print('\nArchivos generados en:', OUT)
    print('TEST NO EVALUADO. El modelo Ridge no se exporta ni despliega en este paso.')


if __name__ == '__main__':
    main()
