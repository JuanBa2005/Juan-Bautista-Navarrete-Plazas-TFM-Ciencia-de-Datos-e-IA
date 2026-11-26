import streamlit as st

from componentes import (
    cabecera,
    menu_operativo,
    pie_pagina,
)


cabecera()
menu_operativo()

st.title("📊 Predicción global")

st.write(
    "Consulta la previsión de consumo de todos "
    "los repuestos para el siguiente mes de referencia."
)

st.warning(
    "Pantalla en fase de integración con el "
    "motor predictivo de TallerPredict."
)

pie_pagina()