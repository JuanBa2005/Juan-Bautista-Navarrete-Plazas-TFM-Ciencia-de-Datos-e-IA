import streamlit as st


def cabecera():
    """Cabecera común de TallerPredict."""
    st.markdown(
        """
        <div style="
            background-color: #142C43;
            padding: 24px;
            border-radius: 12px;
            color: white;
            margin-bottom: 24px;
        ">
            <h1 style="color: white; margin: 0;">
                🔧 TallerPredict
            </h1>
            <p style="color: #CBD5E1; margin: 0;">
                Inteligencia aplicada a la gestión del taller
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pie_pagina():
    """Información académica y versión."""
    st.divider()
    st.caption(
        "TallerPredict · v1.0 MVP · "
        "TFM Ciencia de Datos e Inteligencia Artificial · 2026"
    )


def volver_inicio():
    """Botón de retorno a la página principal."""
    if st.button(
        "🏠 Volver al inicio",
        type="primary",
        use_container_width=True,
        key="volver_inicio",
    ):
        st.switch_page("paginas/inicio.py")


def menu_operativo():
    """Navegación para las pantallas funcionales."""
    opciones = [
        ("🏠 Inicio", "paginas/inicio.py"),
        ("📊 Global", "paginas/prediccion_global.py"),
        ("🔍 Individual", "paginas/prediccion_individual.py"),
        ("🗃️ Datos", "paginas/importar_datos.py"),
        ("🚗 Vehículos", "paginas/prediccion_vehiculos.py"),
    ]

    columnas = st.columns(len(opciones))

    for i, (texto, destino) in enumerate(opciones):
        with columnas[i]:
            if st.button(
                texto,
                key=f"nav_{i}",
                use_container_width=True,
            ):
                st.switch_page(destino)


def tarjeta_funcionalidad(
    titulo,
    descripcion,
    icono,
    destino,
    disponible,
    clave,
):
    """Tarjeta del menú principal."""
    with st.container(border=True):
        st.subheader(f"{icono} {titulo}")

        if disponible:
            st.markdown(":green[● Disponible]")
        else:
            st.markdown(":gray[◷ Próximamente]")

        st.write(descripcion)

        texto_boton = (
            "Acceder →"
            if disponible
            else "Más información →"
        )

        if st.button(
            texto_boton,
            key=clave,
            type="primary" if disponible else "secondary",
            use_container_width=True,
        ):
            st.switch_page(destino)


def pantalla_proximamente(
    titulo,
    icono,
    descripcion,
    funcionalidades,
):
    """Plantilla común para funcionalidades futuras."""
    cabecera()

    with st.container(border=True):
        st.title(f"{icono} {titulo}")

        st.info(
            "Próximamente · Funcionalidad prevista "
            "para una futura versión de TallerPredict."
        )

        st.write(descripcion)
        st.subheader("Funcionalidades previstas")

        for funcionalidad in funcionalidades:
            st.markdown(f"- {funcionalidad}")

        st.divider()
        volver_inicio()

    pie_pagina()


def pantalla_error(mensaje):
    """Estado de error sin navegación secundaria."""
    cabecera()

    st.error(mensaje)
    st.write(
        "No ha sido posible completar la operación. "
        "Regresa al inicio e inténtalo de nuevo."
    )

    volver_inicio()
    pie_pagina()