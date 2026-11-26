from componentes import pantalla_proximamente


pantalla_proximamente(
    titulo="Importación de datos",
    icono="🗃️",
    descripcion=(
        "Esta funcionalidad permitirá incorporar "
        "nuevos conjuntos de datos sin alterar "
        "la información original de TallerPredict."
    ),
    funcionalidades=[
        "Carga de archivos compatibles con el esquema.",
        "Validación de estructura y tipos de datos.",
        "Comprobación de calidad e integridad.",
        "Almacenamiento independiente de los datos.",
        "Actualización de las previsiones de consumo.",
    ],
)