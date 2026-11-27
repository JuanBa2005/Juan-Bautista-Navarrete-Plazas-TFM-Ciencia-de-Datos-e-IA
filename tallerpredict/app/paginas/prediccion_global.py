"""Pantalla global de TallerPredict."""
import logging
import altair as alt
import streamlit as st

from componentes import (
    cabecera,
    menu_operativo,
    pie_pagina,
    pantalla_error,
)
from servicios.datos import cargar_gold, reconstruir_historico
from servicios.predicciones import predecir_global
from servicios.vista_global import (
    filtrar_previsiones,
    preparar_tabla,
    exportar_csv,
    ranking,
)

try:
    previsiones = predecir_global(reconstruir_historico(cargar_gold()))
except (OSError, ValueError) as error:
    logging.getLogger(__name__).warning('No se pudo preparar la previsión: %s', error)
    pantalla_error('No se han podido cargar los datos o calcular las previsiones. Comprueba el dataset Gold.')
    st.stop()

cabecera()
menu_operativo()

st.title("📊 Predicción global")

referencia = previsiones['mes_referencia'].iloc[0]
mes = previsiones['mes_prediccion'].iloc[0]
st.info(f'Muestra histórica. Referencia: {referencia:%m/%Y}. Previsión: {mes:%m/%Y}. No corresponde al mes siguiente a la fecha actual.')
st.caption('Método: media móvil de tres meses · Horizonte: un mes')
a, b, c, d = st.columns(4)
a.metric('Repuestos analizados', len(previsiones))
b.metric('Previsión positiva', int(previsiones['prediccion'].gt(0).sum()))
c.metric('Previsión cero', int(previsiones['prediccion'].eq(0).sum()))
d.metric('Mes previsto', mes.strftime('%m/%Y'))


def limpiar():
    for clave, valor in [('global_buscar', ''), ('global_unidad', 'Todas'), ('global_estado', 'Todos'), ('global_orden', 'Código')]:
        st.session_state[clave] = valor


with st.container(border=True):
    st.subheader('Filtros de búsqueda')
    texto = st.text_input('Código o nombre', key='global_buscar')
    a, b, c = st.columns(3)
    unidad = a.selectbox('Unidad de medida', ['Todas'] + sorted(previsiones['unit'].unique().tolist()), key='global_unidad')
    estado = b.selectbox('Consumo previsto', ['Todos', 'Positivo', 'Cero'], key='global_estado')
    orden = c.selectbox('Ordenar por', ['Código', 'Nombre', 'Mayor previsión', 'Menor previsión'], key='global_orden')
    st.button('Limpiar filtros', on_click=limpiar, key='global_limpiar')

filtradas = filtrar_previsiones(previsiones, texto, None if unidad == 'Todas' else unidad, estado, orden)
st.subheader('Previsiones de consumo')
st.caption(f'{len(filtradas)} de {len(previsiones)} repuestos. Los indicadores superiores corresponden al catálogo completo.')
if orden in ('Mayor previsión', 'Menor previsión') and unidad == 'Todas':
    st.caption('Ordenación por cantidad dentro de cada unidad de medida.')
if filtradas.empty:
    st.warning('No se han encontrado repuestos con estos filtros. Puedes limpiarlos y volver a consultar.')
else:
    tabla = preparar_tabla(filtradas)
    st.dataframe(tabla, hide_index=True, use_container_width=True,
                 column_config={col: st.column_config.NumberColumn(col, format='%.2f') for col in tabla.select_dtypes('number').columns})
    st.download_button('Descargar resultados filtrados (CSV)', exportar_csv(filtradas),
                       file_name=f'previsiones_{mes:%Y-%m}.csv', mime='text/csv', key='global_csv')
    st.subheader('Consultar un repuesto en detalle')
    etiquetas = dict(zip(filtradas['part_code'], filtradas['part_name']))
    codigo = st.selectbox('Seleccionar repuesto', list(etiquetas), format_func=lambda x: f'{x} — {etiquetas[x]}', key='global_repuesto')
    if st.button('Ver predicción individual', type='primary', key='global_ir_individual'):
        st.session_state['repuesto_seleccionado'] = codigo
        st.switch_page('paginas/prediccion_individual.py')

    st.subheader('Repuestos con mayor consumo previsto')
    unidades = sorted(filtradas['unit'].unique().tolist())
    unidad_grafico = st.selectbox('Unidad del gráfico', unidades, key='global_unidad_grafico')
    top = ranking(filtradas, unidad_grafico)
    if top.empty:
        st.info('No hay previsiones positivas para esta unidad con los filtros actuales.')
    else:
        grafico = top.assign(repuesto=top['part_code'] + ' — ' + top['part_name'])
        st.altair_chart(alt.Chart(grafico).mark_bar(color='#176C76').encode(
            x=alt.X('prediccion:Q', title=f'Consumo previsto ({unidad_grafico})'),
            y=alt.Y('repuesto:N', sort='-x', title=None),
            tooltip=['repuesto:N', alt.Tooltip('prediccion:Q', format='.2f'), 'unit:N'],
        ).properties(height=max(140, 32 * len(grafico))), use_container_width=True)
        st.caption(f'Hasta 10 repuestos con previsión positiva, en {unidad_grafico}, dentro de los resultados filtrados.')

st.caption('Las previsiones son estimaciones de consumo, no recomendaciones de compra. Una previsión cero no garantiza ausencia de demanda.')

pie_pagina()