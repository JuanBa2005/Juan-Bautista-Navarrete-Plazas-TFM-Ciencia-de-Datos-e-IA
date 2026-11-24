#!/usr/bin/env python3
"""TallerPredict | Paso 5: Random Forest frente a Ridge y 3 baselines.

Ejecutar desde la raíz del repositorio:
    python scripts/etapa_3/entrenar_random_forest.py

El conjunto de TEST (referencias 2023-09 a 2023-11) NO se entrena,
ni se usa para comparar modelos ni para ajustar hiperparámetros.
Dependencias: pandas, numpy, scikit-learn, matplotlib.
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
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / 'datos' / 'processed' / 'gold_consumo_mensual_repuestos.csv'
OUT = ROOT / 'resultados' / 'ml' / 'random_forest'
TARGET = 'target_next_month_units'
TRAIN_END = pd.Timestamp('2023-05-01')
VAL_END = pd.Timestamp('2023-08-01')
FEATURES = ['part_id', 'lag_1_units', 'lag_2_units', 'lag_3_units',
            'rolling_3_units', 'target_calendar_month']
NUMERIC = [name for name in FEATURES if name != 'part_id']
RF_PARAMS = {'n_estimators': 300, 'max_depth': 12, 'min_samples_leaf': 3,
             'max_features': 1.0, 'random_state': 42, 'n_jobs': -1}
RIDGE_ALPHA = 10.0  # Mismo valor que el Paso 4; comparación controlada.


def leer_y_partir() -> tuple[pd.DataFrame, pd.DataFrame, int]:
    if not GOLD.exists():
        raise FileNotFoundError(f'No se encontró el Gold: {GOLD}')
    df = pd.read_csv(GOLD, parse_dates=['month_date'])
    required = set(FEATURES) - {'target_calendar_month'} | {
        TARGET, 'month_date', 'unit', 'part_code', 'part_name'}
    faltan = required.difference(df.columns)
    if faltan:
        raise ValueError(f'Faltan columnas obligatorias: {sorted(faltan)}')
    if df[list(required)].isna().any().any():
        raise ValueError('Se han detectado nulos en columnas esenciales')
    if df.duplicated(['part_id', 'month_date']).any():
        raise ValueError('Se detectaron repuestos-mes duplicados')
    cols_consumo = ['lag_1_units', 'lag_2_units', 'lag_3_units',
                    'rolling_3_units', TARGET]
    if (df[cols_consumo] < 0).any().any():
        raise ValueError('Se han detectado consumos negativos')
    if not df.groupby('part_id')['unit'].nunique().eq(1).all():
        raise ValueError('Algún repuesto tiene unidades inconsistentes')

    df['target_calendar_month'] = (df['month_date'] + pd.offsets.MonthBegin(1)).dt.month
    df['part_id'] = df['part_id'].astype(str)
    train = df.loc[df['month_date'] <= TRAIN_END].copy()
    valid = df.loc[(df['month_date'] > TRAIN_END) & (df['month_date'] <= VAL_END)].copy()
    n_test = int((df['month_date'] > VAL_END).sum())  # Solo contar filas; NO leer etiquetas.
    if (len(train), len(valid), n_test) != (2160, 240, 240):
        raise ValueError('Particiones inesperadas: se esperaban 2160, 240 y 240 filas')
    if train.month_date.max() >= valid.month_date.min():
        raise ValueError('Las particiones no son cronológicas')
    if not set(valid.part_id).issubset(set(train.part_id)):
        raise ValueError('Hay repuestos de validación sin histórico de entrenamiento')
    return train, valid, n_test


def entrenar_modelos(train: pd.DataFrame, valid: pd.DataFrame) -> dict[str, np.ndarray]:
    x_train, y_train = train[FEATURES], train[TARGET]
    x_valid = valid[FEATURES]
    # Tanto Ridge como RF se ajustan exclusivamente con TRAIN.
    ridge = Pipeline([
        ('preparacion', ColumnTransformer([
            ('repuesto', OneHotEncoder(handle_unknown='ignore'), ['part_id']),
            ('numericas', StandardScaler(), NUMERIC),
        ])),
        ('regresion', Ridge(alpha=RIDGE_ALPHA)),
    ])
    forest = Pipeline([
        ('preparacion', ColumnTransformer([
            ('repuesto', OneHotEncoder(handle_unknown='ignore'), ['part_id']),
            ('numericas', 'passthrough', NUMERIC),
        ])),
        ('regresion', RandomForestRegressor(**RF_PARAMS)),
    ])
    ridge.fit(x_train, y_train)
    forest.fit(x_train, y_train)
    return {
        'siempre_cero': np.zeros(len(valid), dtype=float),
        'ultimo_mes': valid['lag_1_units'].to_numpy(dtype=float),
        'media_tres_meses': valid['rolling_3_units'].to_numpy(dtype=float),
        'ridge': np.maximum(ridge.predict(x_valid), 0.0),
        'random_forest': np.maximum(forest.predict(x_valid), 0.0),
    }


def resumen_modelo(g: pd.DataFrame) -> dict:
    y = g[TARGET].to_numpy(float)
    p = g['prediccion'].to_numpy(float)
    abs_err = np.abs(p-y)
    positivos = y > 0
    ceros = ~positivos
    return {
        'n': len(g),
        'mae_mixto_solo_diagnostico': float(abs_err.mean()),
        'rmse_mixto_solo_diagnostico': float(np.sqrt(np.mean((p-y)**2))),
        'mae_escalado_macro_repuesto': float(g.groupby('part_id')['error_escalado'].mean().mean()),
        'mae_consumo_positivo_mixto_solo_diagnostico': float(abs_err[positivos].mean()) if positivos.any() else None,
        'mae_meses_cero_mixto_solo_diagnostico': float(abs_err[ceros].mean()) if ceros.any() else None,
        'sesgo_mixto_solo_diagnostico': float(np.mean(p-y)),
        'fallos_cero_exacto_ante_positivo': int(np.sum(positivos & (p == 0))),
        'n_consumos_positivos': int(positivos.sum()),
        'n_meses_cero': int(ceros.sum()),
    }


def main() -> None:
    train, valid, n_test = leer_y_partir()
    predicciones = entrenar_modelos(train, valid)
    # Escala calculada con TRAIN; metodología idéntica al Paso 4.
    escala = train.groupby('part_id')[TARGET].mean().clip(lower=1).rename('escala_train')
    valid = valid.merge(escala, on='part_id', how='left', validate='many_to_one')
    if valid['escala_train'].isna().any():
        raise ValueError('Falta una escala de entrenamiento en validación')

    filas = []
    for nombre, pred in predicciones.items():
        g = valid[['part_id', 'part_code', 'part_name', 'unit', 'month_date',
                   TARGET, 'escala_train']].copy()
        g['modelo'] = nombre
        g['prediccion'] = np.maximum(np.asarray(pred, dtype=float), 0)
        g['error'] = g['prediccion'] - g[TARGET]
        g['error_absoluto'] = g['error'].abs()
        g['error_escalado'] = g['error_absoluto'] / g['escala_train']
        g['target_month_date'] = g['month_date'] + pd.offsets.MonthBegin(1)
        filas.append(g)
    pred_df = pd.concat(filas, ignore_index=True)

    resumen = pd.DataFrame([
        {'modelo': nombre, **resumen_modelo(g)}
        for nombre, g in pred_df.groupby('modelo', sort=False)
    ])
    por_unidad = pd.DataFrame([
        {'modelo': nombre, 'unidad': unidad, 'n': len(g),
         'mae': float(g.error_absoluto.mean()),
         'mae_consumo_positivo': float(g.loc[g[TARGET] > 0, 'error_absoluto'].mean())
         if (g[TARGET] > 0).any() else None}
        for (nombre, unidad), g in pred_df.groupby(['modelo', 'unit'], sort=True)
    ])
    por_repuesto = pd.DataFrame([
        {'modelo': nombre, 'part_id': pieza, 'part_code': g.part_code.iloc[0],
         'part_name': g.part_name.iloc[0], 'unidad': g.unit.iloc[0],
         'mae': float(g.error_absoluto.mean()),
         'mae_escalado': float(g.error_escalado.mean())}
        for (nombre, pieza), g in pred_df.groupby(['modelo', 'part_id'], sort=True)
    ])
    peores = (pred_df.loc[pred_df.modelo.eq('random_forest')]
              .sort_values('error_escalado', ascending=False).head(20).copy())
    OUT.mkdir(parents=True, exist_ok=True)
    resumen.round(6).to_csv(OUT / 'metricas_validacion_comparacion.csv', index=False)
    por_unidad.round(6).to_csv(OUT / 'metricas_validacion_por_unidad.csv', index=False)
    por_repuesto.round(6).to_csv(OUT / 'metricas_validacion_por_repuesto.csv', index=False)
    pred_df.to_csv(OUT / 'predicciones_validacion_comparadas.csv', index=False)
    peores.to_csv(OUT / 'mayores_errores_random_forest_validacion.csv', index=False)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    plot = resumen.sort_values('mae_escalado_macro_repuesto')
    ax.bar(plot.modelo, plot.mae_escalado_macro_repuesto)
    ax.set_ylabel('MAE escalado macro por repuesto (menor es mejor)')
    ax.set_title('TallerPredict: 3 baselines, Ridge y Random Forest')
    ax.tick_params(axis='x', rotation=15)
    fig.tight_layout()
    fig.savefig(OUT / '01_comparacion_mae_escalado.png', dpi=150)
    plt.close(fig)

    pivot = por_unidad.pivot(index='unidad', columns='modelo', values='mae')
    ax = pivot.plot.bar(figsize=(10, 5))
    ax.set_ylabel('MAE en la unidad indicada (no agregar unidades)')
    ax.set_title('TallerPredict: errores separados por unidad')
    ax.tick_params(axis='x', rotation=0)
    ax.legend(fontsize=8, title='Modelo')
    fig = ax.figure
    fig.tight_layout()
    fig.savefig(OUT / '02_mae_por_unidad.png', dpi=150)
    plt.close(fig)

    settings = {
        'objetivo': TARGET, 'variables': FEATURES,
        'particion': {'train_end': str(TRAIN_END.date()),
                      'validation_end': str(VAL_END.date()),
                      'n_train': len(train), 'n_validation': len(valid),
                      'n_test_reservado': n_test},
        'ridge_alpha': RIDGE_ALPHA, 'random_forest': RF_PARAMS,
        'criterio_primario_orientativo': 'MAE escalado macro por repuesto usando max(media de target en train, 1)',
        'advertencias': [
            'El modelo no utiliza etiquetas de TEST; TEST sigue reservado.',
            'Los MAE y RMSE mezclados sirven solo como diagnósticos numéricos.',
            'El error en meses positivos no basta para decidir el modelo; mirar también meses cero.',
            'No se han ajustado hiperparámetros de Random Forest con validación.',
            'Las variables rolling_3_units y los tres lags tienen relación determinista; se mantienen por continuidad.',
            'Consumo registrado no equivale necesariamente a demanda real sin roturas de stock.',
        ],
    }
    (OUT / 'configuracion_random_forest.json').write_text(
        json.dumps(settings, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\n=== TALLERPREDICT | PASO 5: RANDOM FOREST ===')
    print(f'Entrenamiento: {len(train)} | Validación: {len(valid)} | Test reservado: {n_test}')
    print('\nCOMPARACIÓN EN VALIDACIÓN (métricas mixtas, SOLO orientativas):')
    cols = ['modelo', 'mae_escalado_macro_repuesto', 'rmse_mixto_solo_diagnostico',
            'mae_consumo_positivo_mixto_solo_diagnostico', 'mae_meses_cero_mixto_solo_diagnostico']
    print(resumen[cols].round(4).to_string(index=False))
    print('\nMAE POR UNIDAD:')
    print(pivot.round(4).to_string())
    print('\nArchivos generados:', OUT)
    print('TEST NO EVALUADO. No se ha elegido modelo definitivo.')


if __name__ == '__main__':
    main()
