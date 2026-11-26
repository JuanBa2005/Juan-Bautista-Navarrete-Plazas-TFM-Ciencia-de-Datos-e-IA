import streamlit as st

from componentes import (
    cabecera,
    pie_pagina,
    tarjeta_funcionalidad,
)


cabecera()

st.title("Panel principal")

st.write(
    "Bienvenido a TallerPredict. Selecciona la "
    "funcionalidad a la que deseas acceder."
)

col1, col2 = st.columns(2, gap="large")

with col1:
    tarjeta_funcionalidad(
        titulo="Predicción global",
        descripcion=(
            "Consulta el consumo previsto de todos "
            "los repuestos para el siguiente mes "
            "de referencia."
        ),
        icono="📊",
        destino="paginas/prediccion_global.py",
        disponible=True,
        clave="inicio_global",
    )

with col2:
    tarjeta_funcionalidad(
        titulo="Predicción individual",
        descripcion=(
            "Analiza el histórico y la previsión "
            "de consumo de un repuesto específico."
        ),
        icono="🔍",
        destino="paginas/prediccion_individual.py",
        disponible=True,
        clave="inicio_individual",
    )

col3, col4 = st.columns(2, gap="large")

with col3:
    tarjeta_funcionalidad(
        titulo="Importación de datos",
        descripcion=(
            "Incorpora nuevos conjuntos de datos "
            "y gestiona sus actualizaciones."
        ),
        icono="🗃️",
        destino="paginas/importar_datos.py",
        disponible=False,
        clave="inicio_datos",
    )

with col4:
    tarjeta_funcionalidad(
        titulo="Predicción de vehículos",
        descripcion=(
            "Anticipa posibles entradas de vehículos "
            "al taller mediante análisis predictivo."
        ),
        icono="🚗",
        destino="paginas/prediccion_vehiculos.py",
        disponible=False,
        clave="inicio_vehiculos",
    )

st.divider()

with st.container(border=True):
    st.subheader("ℹ️ Información del sistema")

    info1, info2, info3 = st.columns(3)

    info1.metric("Repuestos analizados", 80)
    info2.metric("Horizonte predictivo", "1 mes")
    info3.metric("Método", "Media móvil")

    st.caption(
        "Método seleccionado: media móvil de tres meses. "
        "MVP basado en una muestra de datos históricos."
    )

pie_pagina()