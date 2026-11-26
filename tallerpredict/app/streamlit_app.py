import streamlit as st


st.set_page_config(
    page_title="TallerPredict",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Registro de las páginas de la aplicación.
paginas = [
    st.Page(
        "paginas/inicio.py",
        title="Inicio",
        icon="🏠",
        default=True,
    ),
    st.Page(
        "paginas/prediccion_global.py",
        title="Predicción global",
        icon="📊",
    ),
    st.Page(
        "paginas/prediccion_individual.py",
        title="Predicción individual",
        icon="🔍",
    ),
    st.Page(
        "paginas/importar_datos.py",
        title="Importación de datos",
        icon="🗃️",
    ),
    st.Page(
        "paginas/prediccion_vehiculos.py",
        title="Predicción de vehículos",
        icon="🚗",
    ),
]

# Ocultar el menú automático.
# Cada página controla su propia navegación.
navegacion = st.navigation(
    paginas,
    position="hidden",
)

navegacion.run()