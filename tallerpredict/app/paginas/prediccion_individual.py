import streamlit as st

from componentes import (
    cabecera,
    menu_operativo,
    pie_pagina,
)


cabecera()
menu_operativo()

st.title("🔍 Predicción individual")

st.write(
    "Selecciona un repuesto para consultar "
    "su evolución histórica y previsión de consumo."
)

st.warning(
    "Pantalla en fase de integración con el "
    "motor predictivo de TallerPredict."
)

pie_pagina()