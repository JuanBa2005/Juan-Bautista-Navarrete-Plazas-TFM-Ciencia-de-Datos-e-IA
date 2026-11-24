#!/usr/bin/env python3
"""TallerPredict | Paso 6: auditoría de errores y validación temporal creciente.

Desde la raíz del proyecto: python scripts/etapa_3/validar_modelos_temporal.py
No utiliza objetivos de los meses de referencia 2023-09 a 2023-11 (TEST).
Requiere: pandas, numpy, scikit-learn, matplotlib.
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
OUT = ROOT / 'resultados' / 'ml' / 'validacion_temporal'
TARGET = 'target_next_month_units'
FEATURES = ['part_id', 'lag_1_units', 'lag_2_units', 'lag_3_units',
            'rolling_3_units', 'target_calendar_month']
NUMERIC = [c for c in FEATURES if c != 'part_id']
TEST_START = pd.Timestamp('2023-09-01')
FOLDS = [
    ('V1', '2022-08-01', '2022-09-01', '2022-11-01'),
    ('V2', '2022-11-01', '2022-12-01', '2023-02-01'),
    ('V3', '2023-02-01', '2023-03-01', '2023-05-01'),
    ('V4', '2023-05-01', '2023-06-01', '2023-08-01'),
]
RF_PARAMS = dict(n_estimators=300, max_depth=12, min_samples_leaf=3,
                 max_features=1.0, random_state=42, n_jobs=-1)
MODELS = ['siempre_cero', 'ultimo_mes', 'media_tres_meses', 'ridge', 'random_forest']


def load_history() -> pd.DataFrame:
    if not GOLD.is_file():
        raise FileNotFoundError(f'Gold no encontrado: {GOLD}')
    # Se excluyen las filas de test antes de cualquier ajuste o evaluación.
    df = pd.read_csv(GOLD, parse_dates=['month_date'])
    df = df.loc[df.month_date < TEST_START].copy()
    required = set(FEATURES) - {'target_calendar_month'} | {
        'month_date', 'part_code', 'part_name', 'unit', TARGET}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'Columnas faltantes: {sorted(missing)}')
    if df[list(required)].isna().any().any():
        raise ValueError('Valores nulos en columnas esenciales')
    if df.duplicated(['part_id', 'month_date']).any():
        raise ValueError('Pares repuesto-mes duplicados')
    if (df[['lag_1_units', 'lag_2_units', 'lag_3_units', 'rolling_3_units', TARGET]] < 0).any().any():
        raise ValueError('Consumos negativos')
    if not df.groupby('part_id').unit.nunique().eq(1).all():
        raise ValueError('Unidades inconsistentes por repuesto')
    df['part_id'] = df['part_id'].astype(str)
    df['target_calendar_month'] = (df.month_date + pd.offsets.MonthBegin(1)).dt.month
    return df


def estimate(train: pd.DataFrame, validation: pd.DataFrame) -> dict[str, np.ndarray]:
    ridge = Pipeline([
        ('preprocesado', ColumnTransformer([
            ('repuesto', OneHotEncoder(handle_unknown='ignore'), ['part_id']),
            ('numericas', StandardScaler(), NUMERIC),
        ])),
        ('modelo', Ridge(alpha=10.0)),
    ])
    forest = Pipeline([
        ('preprocesado', ColumnTransformer([
            ('repuesto', OneHotEncoder(handle_unknown='ignore'), ['part_id']),
            ('numericas', 'passthrough', NUMERIC),
        ])),
        ('modelo', RandomForestRegressor(**RF_PARAMS)),
    ])
    ridge.fit(train[FEATURES], train[TARGET])
    forest.fit(train[FEATURES], train[TARGET])
    return {
        'siempre_cero': np.zeros(len(validation)),
        'ultimo_mes': validation.lag_1_units.to_numpy(float),
        'media_tres_meses': validation.rolling_3_units.to_numpy(float),
        'ridge': np.maximum(0, ridge.predict(validation[FEATURES])),
        'random_forest': np.maximum(0, forest.predict(validation[FEATURES])),
    }


def summary(group: pd.DataFrame) -> dict:
    pos = group[TARGET] > 0
    zero = ~pos
    err = group.prediccion - group[TARGET]
    mae_unit = group.groupby('part_id').error_escalado.mean()
    return dict(n=int(len(group)),
                mae_escalado_macro_repuesto=float(mae_unit.mean()),
                mae_escalado_macro_repuesto_positivos=(
                    float(group.loc[pos].groupby('part_id').error_escalado.mean().mean())
                    if pos.any() else None),
                mae_escalado_macro_repuesto_ceros=(
                    float(group.loc[zero].groupby('part_id').error_escalado.mean().mean())
                    if zero.any() else None),
                mae_mixto_diagnostico=float(group.error_absoluto.mean()),
                rmse_mixto_diagnostico=float(np.sqrt(np.mean(err**2))),
                sesgo_mixto_diagnostico=float(err.mean()),
                porcentaje_ceros_real=float(zero.mean()*100),
                n_positivos=int(pos.sum()))


def main():
    history = load_history()
    frames = []
    audit = []
    for fold, endtrain, startval, endval in FOLDS:
        endtrain, startval, endval = map(pd.Timestamp, (endtrain, startval, endval))
        train = history.loc[history.month_date <= endtrain].copy()
        val = history.loc[history.month_date.between(startval, endval)].copy()
        if train.empty or val.empty or len(val) != 240 or train.month_date.max() >= val.month_date.min():
            raise ValueError(f'Partición inválida: {fold}')
        if not set(val.part_id).issubset(set(train.part_id)):
            raise ValueError(f'Repuestos nuevos no vistos en {fold}')
        # Cada escala se calcula únicamente a partir del train de su ventana.
        scale = train.groupby('part_id')[TARGET].mean().clip(lower=1).rename('escala_train')
        val = val.merge(scale, on='part_id', validate='many_to_one')
        predictions = estimate(train, val)
        for name, values in predictions.items():
            part = val[['part_id', 'part_code', 'part_name', 'unit', 'month_date',
                        TARGET, 'escala_train']].copy()
            part['fold'] = fold
            part['modelo'] = name
            part['prediccion'] = np.maximum(np.asarray(values, float), 0)
            part['error'] = part.prediccion - part[TARGET]
            part['error_absoluto'] = part.error.abs()
            part['error_escalado'] = part.error_absoluto / part.escala_train
            part['mes_predicho'] = part.month_date + pd.offsets.MonthBegin(1)
            frames.append(part)
        audit.append(dict(fold=fold, train_fin=endtrain.date().isoformat(),
                          validation_inicio=startval.date().isoformat(),
                          validation_fin=endval.date().isoformat(),
                          n_train=len(train), n_validation=len(val)))
        print(f'{fold}: TRAIN={len(train)}, VALIDACIÓN={len(val)}; test intacto')

    results = pd.concat(frames, ignore_index=True)
    folds_metrics = pd.DataFrame([{'fold': f, 'modelo': model, **summary(g)}
                                  for (f, model), g in results.groupby(['fold', 'modelo'], sort=False)])
    # Para comparabilidad de escala, cada fold tiene su propia escala de train.
    pooled_metrics = pd.DataFrame([{'modelo': model, **summary(g)}
                                   for model, g in results.groupby('modelo', sort=False)])
    per_part = pd.DataFrame([
        dict(modelo=model, part_id=part, part_code=g.part_code.iloc[0],
             part_name=g.part_name.iloc[0], unidad=g.unit.iloc[0], n=len(g),
             mae=float(g.error_absoluto.mean()),
             mae_escalado=float(g.error_escalado.mean()),
             n_positivos=int((g[TARGET] > 0).sum()))
        for (model, part), g in results.groupby(['modelo', 'part_id'], sort=True)])
    per_unit = pd.DataFrame([
        dict(modelo=model, unidad=unit, n=len(g), mae=float(g.error_absoluto.mean()),
             sesgo=float(g.error.mean()), porcentaje_ceros=float((g[TARGET] == 0).mean()*100))
        for (model, unit), g in results.groupby(['modelo', 'unit'], sort=True)])
    # Diagnóstico de consumo relevante: una cantidad positiva material por escala.
    # No es un clasificador ni una decisión de compra: solo una evaluación exploratoria.
    threshold_rows = []
    for unit in sorted(results.unit.unique()):
        subset = results[results.unit.eq(unit)]
        for cutoff in (0.0, 0.5, 1.0):
            for model, g in subset.groupby('modelo', sort=False):
                real = g[TARGET].to_numpy() > cutoff
                predicted = g.prediccion.to_numpy() > cutoff
                tp = int((real & predicted).sum())
                fn = int((real & ~predicted).sum())
                fp = int((~real & predicted).sum())
                tn = int((~real & ~predicted).sum())
                threshold_rows.append(dict(unidad=unit, umbral_exploratorio=cutoff,
                                           modelo=model, tp=tp, fn=fn, fp=fp, tn=tn,
                                           sensibilidad=tp/(tp+fn) if tp+fn else np.nan,
                                           precision=tp/(tp+fp) if tp+fp else np.nan))
    threshold_df = pd.DataFrame(threshold_rows)

    # Errores de validación de V4 para comparación con los pasos 4 y 5.
    last = results[(results.fold == 'V4') & (results.modelo == 'random_forest')]
    worst = last.sort_values('error_escalado', ascending=False).head(20).copy()
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(audit).to_csv(OUT/'auditoria_ventanas.csv', index=False)
    folds_metrics.round(6).to_csv(OUT/'metricas_por_ventana.csv', index=False)
    pooled_metrics.round(6).to_csv(OUT/'metricas_globales_ventanas.csv', index=False)
    per_part.round(6).to_csv(OUT/'errores_por_repuesto.csv', index=False)
    per_unit.round(6).to_csv(OUT/'errores_por_unidad.csv', index=False)
    threshold_df.round(6).to_csv(OUT/'analisis_umbrales_exploratorio.csv', index=False)
    worst.round(6).to_csv(OUT/'mayores_errores_rf_ultima_ventana.csv', index=False)
    results.round(6).to_csv(OUT/'predicciones_validacion_temporal.csv', index=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    pivot = folds_metrics.pivot(index='fold', columns='modelo', values='mae_escalado_macro_repuesto')
    pivot = pivot[MODELS]
    pivot.plot(ax=ax, marker='o')
    ax.set_title('TallerPredict: validación con ventanas crecientes')
    ax.set_ylabel('MAE escalado macro por repuesto (menor es mejor)')
    ax.set_xlabel('Ventana de validación')
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(OUT/'01_mae_escalado_por_ventana.png', dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    pooled_metrics.sort_values('mae_escalado_macro_repuesto').plot.bar(
        x='modelo', y='mae_escalado_macro_repuesto', ax=ax, legend=False)
    ax.set_ylabel('MAE escalado macro por repuesto')
    ax.set_title('Comparación global de 4 ventanas')
    ax.tick_params(axis='x', rotation=18)
    fig.tight_layout()
    fig.savefig(OUT/'02_comparacion_global.png', dpi=160)
    plt.close(fig)

    metadata = dict(test_referencia_inicio='2023-09-01',
                    test_reservado='No se utilizan objetivos de referencia desde septiembre de 2023',
                    ventanas=audit, variables=FEATURES, ridge_alpha=10.0,
                    random_forest=RF_PARAMS,
                    advertencias=[
                        'Las escalas se calculan con TRAIN de cada ventana.',
                        'Las métricas mixtas de unidades físicas son solo exploratorias.',
                        'Los umbrales 0, 0.5 y 1 son diagnósticos; no se usan para seleccionar reglas operativas.',
                        'Las predicciones de una ventana comparten datos de entrenamiento con ventanas previas.',
                        'Las magnitudes observadas representan consumo, no necesariamente demanda sin censura.',
                        'No se eligen hiperparámetros a partir del conjunto test.',
                    ])
    (OUT/'configuracion_paso6.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\n=== RESULTADOS PASO 6 ===')
    print('MAE ESCALADO MACRO, por ventana:')
    print(pivot.round(4).to_string())
    print('\nMAE ESCALADO MACRO, conjunto de ventanas:')
    print(pooled_metrics[['modelo','mae_escalado_macro_repuesto']].sort_values('mae_escalado_macro_repuesto').round(4).to_string(index=False))
    print('\nArchivos:', OUT)
    print('TEST RESERVADO, SIN EVALUAR.')


if __name__ == '__main__':
    main()
