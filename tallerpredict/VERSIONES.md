# Versiones y reproducibilidad de TallerPredict

## Etapa actual: esquema e importacion de CSV

- **PostgreSQL:** version recomendada **18.7** (rama 17). Instalar servidor y cliente `psql` de una version compatible. Comprueba `psql --version` y `SELECT version();`.
- **Python:** NO se necesita para `sql/esquema_taller_postgresql.sql` ni `sql/datos_taller.sql`; `\copy` lo ejecuta `psql`.
- **Python futuro:** usar **3.12.10**, indicada en `.python-version` (este archivo no instala Python automaticamente).
- **requirements.txt:** dependencia de conexion desde aplicaciones Python.
- **requirements-ml.txt:** bibliotecas opcionales para cuando se implemente aprendizaje automatico.

## Instalacion opcional de Python

Desde la raiz del proyecto, con Python 3.12.10 instalado:

```bash
python -m venv .venv
```

En Windows PowerShell: `.venv\Scripts\Activate.ps1`.
En Linux/macOS: `source .venv/bin/activate`.

```bash
python -m pip install -r requirements.txt
# Solo cuando sea necesario:
python -m pip install -r requirements-ml.txt
```

## Limites de fijar versiones

`requirements.txt` fija **dependencias directas** con `==`, pero **no** todas las dependencias transitivas, ni la version de PostgreSQL, del sistema operativo o de Python. Para obtener instalaciones Python totalmente reproducibles por plataforma, generar y versionar un archivo de bloqueo con hashes mediante `pip-tools` o `uv`, y probarlo en los sistemas de destino. Dependencias binarias pueden diferir entre Windows, Linux y macOS. Para la misma version de PostgreSQL en distintos equipos, usar contenedores con imagen fijada por version o digest, y planificar actualizaciones de seguridad periodicas. Los nombres de los ficheros existentes y rutas `datos/*.csv` no se modifican.

## Creacion e importacion, sin Python

Desde la raiz `tallerpredict/`:

```bash
createdb -U postgres taller_predict
psql -X -v ON_ERROR_STOP=1 -U postgres -d taller_predict -f sql/esquema_taller_postgresql.sql
psql -X -v ON_ERROR_STOP=1 -U postgres -d taller_predict -f sql/datos_taller.sql
```

La importacion es para tablas vacias; consulta `README.md`.
