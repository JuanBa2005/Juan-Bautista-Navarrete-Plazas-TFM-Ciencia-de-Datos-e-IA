"""Carga y reconstrucción del histórico observado a partir del Gold."""
from pathlib import Path
import numpy as np
import pandas as pd

RUTA_GOLD = (Path(__file__).resolve().parents[2] / 'datos' / 'processed'
             / 'gold_consumo_mensual_repuestos.csv')
IDENTIDAD = ['part_id', 'part_code', 'part_name', 'unit']
CONSUMOS = ['lag_1_units', 'lag_2_units', 'lag_3_units',
            'rolling_3_units', 'target_next_month_units']
COLUMNAS = IDENTIDAD + ['month_date'] + CONSUMOS


def cargar_gold(ruta=RUTA_GOLD):
    """Lee y comprueba el panel mensual sin modificar el archivo."""
    datos = pd.read_csv(ruta, usecols=COLUMNAS)
    if datos.empty or datos.isna().any().any():
        raise ValueError('Gold vacío o con valores nulos.')
    datos['month_date'] = pd.to_datetime(datos['month_date'], errors='raise')
    if not datos['month_date'].dt.is_month_start.all() or not (
        datos['month_date'] == datos['month_date'].dt.normalize()).all():
        raise ValueError('Las fechas deben ser el primer día de cada mes.')
    datos[CONSUMOS] = datos[CONSUMOS].apply(pd.to_numeric, errors='raise')
    if not np.isfinite(datos[CONSUMOS].to_numpy()).all() or (datos[CONSUMOS] < 0).any().any():
        raise ValueError('Consumos no finitos o negativos.')
    if datos.duplicated(['part_id', 'month_date']).any():
        raise ValueError('Duplicados repuesto-mes.')
    catalogo = datos[IDENTIDAD].drop_duplicates()
    if catalogo['part_id'].duplicated().any() or catalogo['part_code'].duplicated().any():
        raise ValueError('Identidad de repuesto incoherente.')
    meses = pd.date_range(datos.month_date.min(), datos.month_date.max(), freq='MS')
    esperado = pd.MultiIndex.from_product([catalogo.part_id, meses])
    real = pd.MultiIndex.from_frame(datos[['part_id', 'month_date']])
    if len(esperado.difference(real)):
        raise ValueError('Faltan combinaciones repuesto-mes.')
    media = datos[['lag_1_units', 'lag_2_units', 'lag_3_units']].mean(axis=1)
    if not np.allclose(media, datos['rolling_3_units'], atol=0.0001, rtol=0):
        raise ValueError('Media móvil incoherente con los consumos.')
    return datos.sort_values(['part_id', 'month_date']).reset_index(drop=True)


def reconstruir_historico(gold):
    """Recupera consumos observados y comprueba coincidencias solapadas."""
    bloques = []
    for columna, desplazamiento in [('lag_3_units', -2), ('lag_2_units', -1),
                                     ('lag_1_units', 0), ('target_next_month_units', 1)]:
        bloque = gold[IDENTIDAD + ['month_date', columna]].copy()
        bloque['month_date'] += pd.DateOffset(months=desplazamiento)
        bloque = bloque.rename(columns={columna: 'consumo'})
        bloques.append(bloque)
    historico = pd.concat(bloques, ignore_index=True)
    grupos = historico.groupby(['part_id', 'month_date'])['consumo']
    if ((grupos.max() - grupos.min()) > 0.0001).any():
        raise ValueError('Los consumos históricos solapados no coinciden.')
    return (historico.drop_duplicates(['part_id', 'month_date'])
            .sort_values(['part_id', 'month_date']).reset_index(drop=True))
