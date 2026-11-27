"""Operaciones de presentación de la previsión global, sin modificar el motor."""
import pandas as pd


def filtrar_previsiones(tabla, texto='', unidad=None, estado='Todos', orden='Código'):
    texto = texto.strip()
    mascara = (tabla['part_code'].astype(str).str.contains(texto, case=False, regex=False)
               | tabla['part_name'].astype(str).str.contains(texto, case=False, regex=False))
    if unidad is not None:
        mascara &= tabla['unit'].eq(unidad)
    if estado == 'Positivo':
        mascara &= tabla['prediccion'].gt(0)
    elif estado == 'Cero':
        mascara &= tabla['prediccion'].eq(0)
    resultado = tabla.loc[mascara].copy()
    if orden == 'Mayor previsión':
        return resultado.sort_values(['unit', 'prediccion', 'part_code'], ascending=[True, False, True])
    if orden == 'Menor previsión':
        return resultado.sort_values(['unit', 'prediccion', 'part_code'], ascending=[True, True, True])
    if orden == 'Nombre':
        return resultado.sort_values(['part_name', 'part_code'])
    return resultado.sort_values('part_code')


def preparar_tabla(tabla):
    referencia = tabla['mes_referencia'].iloc[0] if not tabla.empty else None
    nombres = {'part_code': 'Código', 'part_name': 'Repuesto', 'unit': 'Unidad', 'prediccion': 'Previsión'}
    for col, offset in [('consumo_t_2', 2), ('consumo_t_1', 1), ('consumo_t', 0)]:
        nombres[col] = (referencia - pd.DateOffset(months=offset)).strftime('%m/%Y') if referencia is not None else col
    return tabla[list(nombres)].rename(columns=nombres)


def exportar_csv(tabla):
    columnas = ['part_code', 'part_name', 'unit', 'mes_referencia', 'mes_prediccion', 'consumo_t_2', 'consumo_t_1', 'consumo_t', 'prediccion']
    return tabla[columnas].to_csv(index=False, sep=';', decimal=',', date_format='%Y-%m-%d').encode('utf-8-sig')


def ranking(tabla, unidad, limite=10):
    return (tabla.loc[tabla['unit'].eq(unidad) & tabla['prediccion'].gt(0)]
            .sort_values(['prediccion', 'part_code'], ascending=[False, True]).head(limite))
