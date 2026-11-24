# TallerPredict — Código, datos y resultados

Este directorio reúne los datos históricos de muestra, su preparación, los experimentos de Machine Learning y los SQL de importación a PostgreSQL. La documentación académica está **fuera de esta carpeta**, en `../docs/entregas/`.

## Estructura actual

```text
tallerpredict/
├── datos/                # siete CSV de origen y processed/ (Silver, Gold, informe de calidad)
├── scripts/
│   ├── etapa_2/          # preparar_datos.py
│   └── etapa_3/          # EDA, particiones, baselines, Ridge, Random Forest,
│                        # validación temporal, protocolo y verificación
├── resultados/ml/       # resultados de las ocho fases experimentales
├── sql/                 # esquema e importación PostgreSQL
├── requirements.txt
├── requirements-ml.txt
├── .python-version
└── VERSIONES.md
```

## Importación (PostgreSQL, con `psql`)

1. Abre una terminal **en la carpeta `tallerpredict`** (la que contiene `sql/`, `datos/` y `validacion_datos_taller.json`).
2. Crea la base de datos si no existe (por ejemplo, `createdb -U postgres taller_predict`).
3. Ejecuta:

```powershell
psql -X -v ON_ERROR_STOP=1 -U postgres -d taller_predict -f sql/esquema_taller_postgresql.sql
psql -X -v ON_ERROR_STOP=1 -U postgres -d taller_predict -f sql/datos_taller.sql
```

```bash
psql -X -v ON_ERROR_STOP=1 -U postgres -d taller_predict -f sql/esquema_taller_postgresql.sql
psql -X -v ON_ERROR_STOP=1 -U postgres -d taller_predict -f sql/datos_taller.sql
```

**Importante:** `\copy` es una orden del cliente `psql`, no una sentencia SQL estándar; no funcionará pegándola en el editor de consultas de pgAdmin. Las rutas `datos/*.csv` se resuelven respecto del directorio desde el que ejecutas `psql`. `\copy` lee los archivos desde tu ordenador y no requiere privilegios de superusuario ni acceso del servidor a la carpeta. Se ejecuta sobre **tablas vacías**: repetir la importación sobre las mismas tablas dará errores de claves únicas/primarias.

Los CSV incluyen `id` y el mecanismo `COPY FROM` de PostgreSQL acepta los valores explícitos de una columna `GENERATED ALWAYS AS IDENTITY`; el script sincroniza después las secuencias para futuras inserciones. Todas las cargas y las verificaciones de cantidad se ejecutan dentro de una sola transacción.

Si la base de datos usa otro esquema en vez de `public`, adapta los prefijos `public.` del SQL de carga.
