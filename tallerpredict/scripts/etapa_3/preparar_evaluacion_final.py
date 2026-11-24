#!/usr/bin/env python3
"""TallerPredict | Paso 7: protocolo previo a la evaluación final.

Uso seguro (NO lee los objetivos de test):
    python scripts/etapa_3/preparar_evaluacion_final.py

Solo cuando se decida abrir formalmente el test (Paso 8):
    python scripts/etapa_3/preparar_evaluacion_final.py --ejecutar-evaluacion-final

En modo final calcula los resultados una única vez, bloquea la sobrescritura y
no cambia el modelo elegido según los resultados del test.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / 'datos' / 'processed' / 'gold_consumo_mensual_repuestos.csv'
OUT = ROOT / 'resultados' / 'ml' / 'evaluacion_final'
CONFIG = ROOT / 'resultados' / 'ml' / 'protocolo_final' / 'protocolo_paso7.json'
TRAIN_END = pd.Timestamp('2023-08-01')
TEST_START = pd.Timestamp('2023-09-01')
TEST_END = pd.Timestamp('2023-11-01')
TARGET = 'target_next_month_units'
FEATURES = ['part_id', 'lag_1_units', 'lag_2_units', 'lag_3_units',
            'rolling_3_units', 'target_calendar_month']

PROTOCOL = {
    'version': '1.0-paso7-congelado',
    'origen': 'datos/processed/gold_consumo_mensual_repuestos.csv',
    'momento_prediccion': 'Cierre del mes de referencia',
    'objetivo': TARGET,
    'entrenamiento_final': '2021-03 a 2023-08 (30 meses de referencia)',
    'test_referencia': '2023-09 a 2023-11 (3 meses)',
    'test_meses_predichos': '2023-10 a 2023-12',
    'seleccionado': 'media_tres_meses',
    'referencia': 'siempre_cero',
    'candidato_ml_secundario': 'random_forest',
    'metrica_primaria': 'MAE escalado macro por repuesto',
    'escala': 'max(media objetivo por repuesto en entrenamiento final, 1)',
    'criterio_predefinido': 'MAE escalado de media_tres_meses <= 0.95 * MAE escalado de siempre_cero',
    'metricas_secundarias': [
        'MAE escalado macro sobre observaciones positivas por repuesto',
        'MAE por unidad', 'Sesgo por unidad', 'Porcentaje de observaciones positivas',
        'Análisis de grandes errores y repuestos',
    ],
    'precauciones': [
        'No se usa el test para elegir algoritmo, umbral ni hiperparámetros.',
        'Los errores globales sin escala mezclan unidades físicas; solo diagnósticos.',
        'No se demuestra utilidad para compras sin stocks ni costes de error.',
        'El criterio del 5 % es una regla operativa propuesta, no requisito académico ni validado por el taller.',
        'Las predicciones no negativas se obtienen recortando a 0.',
    ],
}


def preflight() -> None:
    if not GOLD.is_file():
        raise FileNotFoundError(f'No se encuentra Gold: {GOLD}')
    # Intencionadamente NO se lee la columna objetivo (ni siquiera del train).
    d = pd.read_csv(GOLD, usecols=['part_id', 'month_date', 'unit', 'lag_1_units',
                                   'lag_2_units', 'lag_3_units', 'rolling_3_units'],
                    parse_dates=['month_date'])
    if d.isna().any().any() or d.duplicated(['part_id', 'month_date']).any():
        raise ValueError('Nulos o duplicados en columnas de entrada')
    train, test = d.loc[d.month_date <= TRAIN_END], d.loc[d.month_date.between(TEST_START, TEST_END)]
    if len(train) != 2400 or len(test) != 240 or train.part_id.nunique() != 80 or test.part_id.nunique() != 80:
        raise ValueError(f'Particiones inesperadas: train={len(train)}, test={len(test)}')
    if not test.part_id.isin(train.part_id).all():
        raise ValueError('Hay repuestos en test que no aparecen en entrenamiento')
    if d.month_date.min() != pd.Timestamp('2021-03-01') or d.month_date.max() != TEST_END:
        raise ValueError('Intervalo de fechas del Gold distinto al previsto')
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG.exists():
        previous = json.loads(CONFIG.read_text(encoding='utf-8'))
        if previous != PROTOCOL:
            raise RuntimeError('Existe un protocolo distinto: revisar antes de continuar')
    else:
        CONFIG.write_text(json.dumps(PROTOCOL, indent=2, ensure_ascii=False), encoding='utf-8')
    print('=== PASO 7: PROTOCOLO VERIFICADO ===')
    print(f'Entrenamiento final: {len(train)} registros | test reservado: {len(test)}')
    print('Candidata seleccionada: media de tres meses')
    print('Referencia: siempre cero | comparación secundaria: Random Forest')
    print('Métrica principal: MAE escalado macro por repuesto')
    print('Importante: NO SE HA LEÍDO NI EVALUADO EL OBJETIVO DE TEST.')
    print(f'Protocolo guardado en: {CONFIG}')


def mae_escalado_macro(d: pd.DataFrame) -> float:
    by_part = d.groupby('part_id', sort=True)['error_escalado'].mean()
    return float(by_part.mean())


def evaluate_final() -> None:
    # Esta función solo se ejecuta tras pasar un indicador explícito.
    if not CONFIG.exists():
        raise RuntimeError('Primero ejecutar sin argumentos para registrar el protocolo del Paso 7')
    frozen = json.loads(CONFIG.read_text(encoding='utf-8'))
    if frozen != PROTOCOL:
        raise RuntimeError('El protocolo congelado no coincide con este script')
    if (OUT / 'metricas_test.csv').exists():
        raise FileExistsError('Ya hay métricas finales. No se permite sobrescribir ni repetir con este script.')

    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder

    d = pd.read_csv(GOLD, parse_dates=['month_date'])
    if TARGET not in d.columns:
        raise ValueError(f'Falta columna objetivo: {TARGET}')
    if d.duplicated(['part_id', 'month_date']).any() or d[TARGET].isna().any():
        raise ValueError('Gold inválido: duplicados o objetivos nulos')
    d['part_id'] = d['part_id'].astype(str)
    d['target_calendar_month'] = (d.month_date + pd.offsets.MonthBegin(1)).dt.month
    train = d.loc[d.month_date <= TRAIN_END].copy()
    test = d.loc[d.month_date.between(TEST_START, TEST_END)].copy()
    if len(train) != 2400 or len(test) != 240:
        raise ValueError('Tamaños inesperados')
    scales = train.groupby('part_id')[TARGET].mean().clip(lower=1).rename('escala_train')
    test = test.join(scales, on='part_id')
    if test.escala_train.isna().any():
        raise ValueError('No se pudo asignar escala a todos los repuestos')

    # El modelo secundario se entrena con la misma configuración congelada del Paso 5.
    rf = Pipeline([
        ('prep', ColumnTransformer([
            ('repuesto', OneHotEncoder(handle_unknown='ignore'), ['part_id']),
            ('numericas', 'passthrough', [x for x in FEATURES if x != 'part_id']),
        ])),
        ('modelo', RandomForestRegressor(n_estimators=300, max_depth=12,
                                        min_samples_leaf=3, max_features=1.0,
                                        random_state=42, n_jobs=-1))
    ])
    rf.fit(train[FEATURES], train[TARGET])
    models = {
        'siempre_cero': np.zeros(len(test), dtype=float),
        'media_tres_meses': test['rolling_3_units'].to_numpy(dtype=float),
        'random_forest': np.maximum(0, rf.predict(test[FEATURES])),
    }
    rows, metrics = [], []
    for model, predictions in models.items():
        frame = test[['part_id', 'part_code', 'part_name', 'unit', 'month_date', TARGET, 'escala_train']].copy()
        frame['modelo'] = model
        frame['prediccion'] = np.maximum(predictions, 0)
        frame['error'] = frame['prediccion'] - frame[TARGET]
        frame['error_absoluto'] = frame['error'].abs()
        frame['error_escalado'] = frame['error_absoluto'] / frame['escala_train']
        rows.append(frame)
        positives = frame.loc[frame[TARGET] > 0]
        metrics.append({
            'modelo': model,
            'n': int(len(frame)),
            'mae_escalado_macro_repuesto': mae_escalado_macro(frame),
            'mae_escalado_macro_positivos': (mae_escalado_macro(positives) if not positives.empty else None),
            'n_positivos': int(len(positives)),
        })
    predictions = pd.concat(rows, ignore_index=True)
    table = pd.DataFrame(metrics)
    zero = float(table.loc[table.modelo == 'siempre_cero', 'mae_escalado_macro_repuesto'].iloc[0])
    selected = float(table.loc[table.modelo == 'media_tres_meses', 'mae_escalado_macro_repuesto'].iloc[0])
    decision = {
        'modelo_preseleccionado': 'media_tres_meses',
        'supera_umbral_5pct_frente_a_cero': bool(selected <= 0.95 * zero),
        'mejora_relativa_frente_a_cero_pct': float((zero - selected) / zero * 100) if zero else None,
        'advertencia': 'La utilidad de inventario no queda demostrada por estas métricas; no ajustar el modelo a test.',
    }
    OUT.mkdir(parents=True, exist_ok=True)
    table.round(6).to_csv(OUT / 'metricas_test.csv', index=False)
    predictions.round(6).to_csv(OUT / 'predicciones_test.csv', index=False)
    unit_metrics = predictions.groupby(['modelo', 'unit'], as_index=False).agg(
        n=('error_absoluto', 'size'), mae=('error_absoluto', 'mean'), sesgo=('error', 'mean'))
    unit_metrics.round(6).to_csv(OUT / 'metricas_test_por_unidad.csv', index=False)
    (OUT / 'decision_test.json').write_text(json.dumps(decision, indent=2, ensure_ascii=False), encoding='utf-8')
    print('\n=== EVALUACIÓN FINAL: TEST ABIERTO ===')
    print(table.to_string(index=False))
    print(f'Conclusión criterio 5 %: {decision["supera_umbral_5pct_frente_a_cero"]}')
    print('No cambiar la elección del modelo utilizando estos resultados.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ejecutar-evaluacion-final', action='store_true',
                        help='ABRE el test: reservar para el Paso 8, una vez aprobado el protocolo')
    args = parser.parse_args()
    if args.ejecutar_evaluacion_final:
        evaluate_final()
    else:
        preflight()


if __name__ == '__main__':
    main()
