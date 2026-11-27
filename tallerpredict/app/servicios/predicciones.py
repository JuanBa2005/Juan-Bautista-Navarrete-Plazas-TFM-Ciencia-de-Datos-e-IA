"""Motor común de previsión mensual: media móvil de tres meses."""
import pandas as pd
from .datos import IDENTIDAD


def predecir_global(historico):
    """Pronostica el mes posterior al último mes observado de la muestra."""
    if historico.empty:
        raise ValueError('No hay histórico disponible.')
    referencia = historico['month_date'].max()
    meses = pd.date_range(end=referencia, periods=3, freq='MS')
    ventana = historico[historico['month_date'].isin(meses)]
    conteo = ventana.groupby('part_id')['month_date'].nunique()
    if (ventana.duplicated(['part_id', 'month_date']).any()
            or len(conteo) != historico['part_id'].nunique()
            or not conteo.eq(3).all()):
        raise ValueError('Se necesitan tres meses consecutivos por repuesto.')
    tabla = ventana.pivot(index=IDENTIDAD, columns='month_date', values='consumo')
    tabla = tabla.reindex(columns=meses)
    tabla.columns = ['consumo_t_2', 'consumo_t_1', 'consumo_t']
    if tabla.isna().any().any():
        raise ValueError('Histórico incompleto en la ventana de previsión.')
    tabla['prediccion'] = tabla.mean(axis=1)
    tabla = tabla.reset_index()
    tabla['mes_referencia'] = referencia
    tabla['mes_prediccion'] = referencia + pd.DateOffset(months=1)
    return tabla.sort_values('part_code').reset_index(drop=True)


def predecir_individual(historico, part_code):
    """Devuelve exactamente la misma previsión que la consulta global."""
    global_ = predecir_global(historico)
    fila = global_[global_['part_code'] == part_code]
    if fila.empty:
        raise ValueError(f'Repuesto no encontrado: {part_code}')
    return fila.iloc[0].copy()


def obtener_historico(historico, part_code):
    """Recupera la serie mensual observada de un repuesto."""
    serie = historico[historico['part_code'] == part_code].copy()
    if serie.empty:
        raise ValueError(f'Repuesto no encontrado: {part_code}')
    return serie.sort_values('month_date').reset_index(drop=True)
