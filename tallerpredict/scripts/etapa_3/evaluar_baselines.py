#!/usr/bin/env python3
"""TallerPredict | Paso 3: evaluación de baselines SIN entrenar modelos ML.

Ejecutar desde cualquier ubicación:
    python scripts/etapa_3/evaluar_baselines.py

Usa exclusivamente etiquetas de TRAIN y VALIDATION; TEST permanece reservado.
Requiere pandas, numpy y matplotlib.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Generar figuras sin abrir ventanas.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / 'datos' / 'processed' / 'gold_consumo_mensual_repuestos.csv'
OUT = ROOT / 'resultados' / 'ml' / 'baselines'
TARGET = 'target_next_month_units'
TRAIN_END = pd.Timestamp('2023-05-01')
VAL_END = pd.Timestamp('2023-08-01')
MODELS = {
    'siempre_cero': None,
    'ultimo_mes': 'lag_1_units',
    'media_tres_meses': 'rolling_3_units',
}


def metrics(g: pd.DataFrame) -> dict:
    y = g[TARGET].to_numpy(dtype=float)
    p = g['prediccion'].to_numpy(dtype=float)
    error = p - y
    positive = y > 0
    false_zero = positive & (p == 0)
    return {
        'n': int(len(g)),
        'mae': float(np.abs(error).mean()),
        'rmse': float(np.sqrt(np.square(error).mean())),
        'sesgo_medio': float(error.mean()),  # >0: sobreestima; <0: infraestima
        'porcentaje_reales_cero': float((~positive).mean() * 100),
        'mae_consumo_positivo': float(np.abs(error[positive]).mean()) if positive.any() else None,
        'fallos_cero_ante_consumo_positivo': int(false_zero.sum()),
        'porcentaje_fallos_cero_sobre_positivos': float(false_zero.sum() / positive.sum() * 100) if positive.any() else None,
        'wape_porcentaje': float(np.abs(error).sum() / y.sum() * 100) if y.sum() > 0 else None,
    }


def main() -> None:
    if not GOLD.exists():
        raise FileNotFoundError(f'Gold no encontrado: {GOLD}')
    df = pd.read_csv(GOLD, parse_dates=['month_date'])
    required = {'part_id', 'part_code', 'part_name', 'unit', 'month_date', TARGET,
                'lag_1_units', 'rolling_3_units'}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f'Columnas que faltan en Gold: {sorted(missing)}')
    if df[list(required)].isna().any().any():
        raise ValueError('Hay nulos en las columnas esenciales')
    if df.duplicated(['part_id', 'month_date']).any():
        raise ValueError('Hay filas duplicadas por repuesto y mes')
    if (df[[TARGET, 'lag_1_units', 'rolling_3_units']] < 0).any().any():
        raise ValueError('Existen consumos negativos; revise Gold')
    if not df.groupby('part_id')['unit'].nunique().eq(1).all():
        raise ValueError('Una pieza presenta distintas unidades de medida')

    # La separación temporal es IDENTICA a la del Paso 2.
    train = df.loc[df['month_date'] <= TRAIN_END].copy()
    validation = df.loc[(df['month_date'] > TRAIN_END) & (df['month_date'] <= VAL_END)].copy()
    # No inspeccionamos ni evaluamos etiquetas de TEST.
    n_test = int((df['month_date'] > VAL_END).sum())
    if train.empty or validation.empty or n_test == 0:
        raise ValueError('Particiones incompletas; revise fechas y Gold')
    if train['month_date'].max() >= validation['month_date'].min():
        raise ValueError('Las particiones no siguen el orden temporal')

    # Escala fija por pieza, definida SOLO con TRAIN.
    # El suelo 1 evita divisiones entre cero y limita amplificaciones exageradas.
    # Esta escala es una convención de comparabilidad, no una unidad física.
    train_scale = train.groupby('part_id')[TARGET].mean().clip(lower=1).rename('escala_train')
    val_base = validation.merge(train_scale, on='part_id', how='left', validate='many_to_one')
    if val_base.escala_train.isna().any():
        raise ValueError('Hay repuestos de validación no vistos en entrenamiento')

    rows = []
    for name, col in MODELS.items():
        g = val_base.copy()
        g['modelo'] = name
        g['prediccion'] = 0.0 if col is None else g[col].astype(float).clip(lower=0)
        g['error'] = g['prediccion'] - g[TARGET]
        g['error_absoluto'] = g['error'].abs()
        g['error_absoluto_escalado'] = g['error_absoluto'] / g['escala_train']
        rows.append(g)
    predictions = pd.concat(rows, ignore_index=True)

    overall = pd.DataFrame([{'modelo': name, **metrics(g),
                             'mae_escalado_macro_repuesto': float(g.groupby('part_id')['error_absoluto_escalado'].mean().mean())}
                            for name, g in predictions.groupby('modelo', sort=False)])
    by_unit = pd.DataFrame([{'modelo': model, 'unidad': unit, **metrics(g)}
                            for (model, unit), g in predictions.groupby(['modelo', 'unit'], sort=True)])
    by_part = pd.DataFrame([{'modelo': model, 'part_id': int(part),
                            'part_code': g['part_code'].iloc[0], 'part_name': g['part_name'].iloc[0],
                            'unidad': g['unit'].iloc[0], **metrics(g),
                            'mae_escalado': float(g['error_absoluto_escalado'].mean())}
                           for (model, part), g in predictions.groupby(['modelo', 'part_id'], sort=True)])
    # Los mejores resultados según métricas distintas pueden no coincidir.
    best = overall.sort_values(['mae_escalado_macro_repuesto', 'modelo']).iloc[0]['modelo']
    top_errors = (predictions.loc[predictions['modelo'].eq(best)]
                  .sort_values('error_absoluto_escalado', ascending=False)
                  .head(20)[['part_id', 'part_code', 'part_name', 'unit', 'month_date',
                             TARGET, 'prediccion', 'error', 'error_absoluto',
                             'escala_train', 'error_absoluto_escalado']].copy())
    top_errors['target_month_date'] = top_errors['month_date'] + pd.offsets.MonthBegin(1)

    OUT.mkdir(parents=True, exist_ok=True)
    overall.round(5).to_csv(OUT / 'metricas_validacion_resumen.csv', index=False)
    by_unit.round(5).to_csv(OUT / 'metricas_validacion_por_unidad.csv', index=False)
    by_part.round(5).to_csv(OUT / 'metricas_validacion_por_repuesto.csv', index=False)
    predictions[['modelo', 'part_id', 'part_code', 'part_name', 'unit',
                 'month_date', TARGET, 'prediccion', 'error', 'error_absoluto',
                 'escala_train', 'error_absoluto_escalado']].to_csv(
        OUT / 'predicciones_validacion.csv', index=False)
    top_errors.to_csv(OUT / 'mayores_errores_escalados_validacion.csv', index=False)

    # Visualizamos la métrica comparable por repuesto y los MAE por unidad.
    fig, ax = plt.subplots(figsize=(8, 4.5))
    z = overall.sort_values('mae_escalado_macro_repuesto')
    ax.bar(z['modelo'], z['mae_escalado_macro_repuesto'])
    ax.set_ylabel('MAE / max(media TRAIN por repuesto, 1)')
    ax.set_title('Comparación de baselines (validación)')
    ax.tick_params(axis='x', rotation=15)
    fig.tight_layout()
    fig.savefig(OUT / '01_comparacion_mae_escalado.png', dpi=150)
    plt.close(fig)

    pivot = by_unit.pivot(index='unidad', columns='modelo', values='mae')
    ax = pivot.plot.bar(figsize=(9, 5))
    ax.set_title('MAE en validación, separado por unidad')
    ax.set_xlabel('Unidad de medida')
    ax.set_ylabel('MAE en la unidad indicada')
    ax.tick_params(axis='x', rotation=0)
    ax.legend(title='Baseline')
    fig = ax.figure
    fig.tight_layout()
    fig.savefig(OUT / '02_mae_por_unidad.png', dpi=150)
    plt.close(fig)

    meta = {
        'gold': str(GOLD.relative_to(ROOT)), 'objetivo': TARGET,
        'periodos_referencia': {
            'train': [str(train.month_date.min().date()), str(train.month_date.max().date())],
            'validation': [str(validation.month_date.min().date()), str(validation.month_date.max().date())],
        },
        'filas_train': len(train), 'filas_validacion': len(validation),
        'filas_test_reservadas_sin_evaluar': n_test,
        'baselines': {'siempre_cero': '0', 'ultimo_mes': 'lag_1_units',
                      'media_tres_meses': 'rolling_3_units'},
        'criterio_comparacion_orientativo': 'media sobre piezas del MAE validación / max(media objetivo TRAIN pieza, 1)',
        'mejor_baseline_segun_criterio_orientativo': str(best),
        'cautelas': ['Las unidades no son agregables entre sí.',
                    'Un buen error medio puede ocultar fallos en consumos positivos.',
                    'No usar etiquetas de TEST para elegir baselines ni hiperparámetros.',
                    'La comparabilidad del MAE escalado depende del suelo de 1 unidad.']
    }
    (OUT / 'resumen_baselines.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
    print('\n=== TALLERPREDICT | PASO 3: BASELINES ===')
    print(f'Train: {len(train)} filas | Validación: {len(validation)} filas | Test reservado: {n_test} filas')
    print('\nComparación orientativa de baselines en VALIDACIÓN:')
    print(overall[['modelo', 'mae_escalado_macro_repuesto', 'mae', 'rmse',
                   'mae_consumo_positivo', 'porcentaje_fallos_cero_sobre_positivos']].round(4).to_string(index=False))
    print('\nMAE por unidad (valores en unidades nativas, NO comparables entre filas):')
    print(pivot.round(4).to_string())
    print('\nBaseline mejor por métrica escalada ORIENTATIVA:', best)
    print('Resultados guardados en:', OUT)
    print('TEST NO EVALUADO. No se ha entrenado ningún modelo de ML.')


if __name__ == '__main__':
    main()
