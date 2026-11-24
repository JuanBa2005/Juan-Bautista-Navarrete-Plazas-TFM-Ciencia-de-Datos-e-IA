# Versiones y reproducibilidad de TallerPredict

## Estado actual

- **Etapa 02:** preparación local de CSV a Silver/Gold mediante `scripts/etapa_2/preparar_datos.py`.
- **Etapa 03:** análisis exploratorio, baselines, Ridge, Random Forest, validación temporal y test final **ya ejecutado**; código en `scripts/etapa_3/`.
- **PostgreSQL:** el repositorio incluye SQL y la Entrega 02 describe la carga de los siete CSV. El ML no requiere conexión a la base de datos.
- **Python declarado:** `3.12.10` en `.python-version`; es una especificación del proyecto, no una confirmación de la versión usada en cada experimento previo.

## Dependencias declaradas

- `requirements.txt`: `psycopg[binary]` para conexión Python/PostgreSQL.
- `requirements-ml.txt`: importa `requirements.txt` e incluye pandas, NumPy, scikit-learn y **Matplotlib**. En la versión revisada **ya estaba incluida Matplotlib**; no es necesaria otra modificación para este motivo.

## Instalación desde `tallerpredict/`

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-ml.txt
python scripts/etapa_3/verificar_entrega_03.py
```

Las versiones directas están fijadas en los archivos `requirements*.txt`, pero **no constituyen un lockfile completo con hashes**. La reproducibilidad bit a bit entre plataformas y fechas requiere controlar también dependencias transitivas, binarios, sistema operativo y versión de Python. Las salidas guardadas proporcionan evidencia verificable; sin embargo, volver a entrenar puede dar pequeñas diferencias por entorno y librerías.

## Reproducción de las fases y preservación del test

Consultar `../docs/entregas/03_machine_learning.md` para el orden exacto de scripts. Conservar `resultados/ml/protocolo_final/protocolo_paso7.json` y `resultados/ml/evaluacion_final/` como evidencias ya consolidadas.

**No lanzar de nuevo** `python scripts/etapa_3/preparar_evaluacion_final.py --ejecutar-evaluacion-final`: esa operación ya se completó en el Paso 8. Para auditar los archivos sin reentrenar, ejecutar `python scripts/etapa_3/verificar_entrega_03.py`.

## Datos de la muestra

La divulgación está condicionada por la autorización documentada en la Entrega 02, que permite utilizar/publicar la muestra cedida sin revelar identificadores privados ni el nombre comercial del taller. Un repositorio público exige comprobar esa condición antes de incluir registros, CSV o predicciones individualizadas.
