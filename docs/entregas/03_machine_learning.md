# Proyecto final — Entrega 03: Machine Learning

**Producto:** TallerPredict  
**Proyecto:** TFM de Ciencia de Datos e Inteligencia Artificial  
**Estado:** experimentos concluidos, evaluación final registrada y decisión para el MVP documentada.  
**Documento anterior:** [`02_datos_y_preparacion.md`](02_datos_y_preparacion.md).  
**Ubicación en el repositorio:** `docs/entregas/03_machine_learning.md` (la carpeta `docs/` está **en la raíz del repositorio**, al mismo nivel que `tallerpredict/`).

> **Resumen ejecutivo.** TallerPredict estudia cómo anticipar el **consumo observado de cada repuesto en el mes siguiente**, para apoyar la planificación del responsable del taller. Partiendo del dataset Gold de la Entrega 02, se analizaron tres baselines y dos modelos supervisados (Ridge y Random Forest), con particiones cronológicas y cuatro ventanas de validación creciente. Se seleccionó **la media móvil de tres meses** mediante validación temporal y antes de examinar la prueba final. En los 240 registros de test alcanzó un **MAE escalado macro por repuesto de 0,501480**, frente a **0,701927** para predecir siempre cero: una mejora del **28,56 %**, superior al umbral de 5 % fijado previamente. Esta evidencia apoya su uso como **estimación orientativa** dentro del MVP; no demuestra por sí sola que sirva para emitir pedidos de reposición automáticos.

## 1. Qué problema resuelve el modelo

### Funcionalidad, usuario y decisión

El objetivo del producto es estimar, **al cierre de cada mes**, cuánto se utilizará de **cada repuesto durante el mes posterior**. El usuario principal es el **responsable del taller o del almacén**, que consultará previsiones para contrastarlas con el inventario y planificar pedidos.

La pregunta que responde esta primera funcionalidad es: **«¿Qué consumo mensual se prevé para cada repuesto el próximo mes?»**. No debe confundirse con «¿cuánto hay que comprar?»; esta segunda decisión requiere, al menos, stock disponible, pedidos en curso, plazos reales de entrega, costes de errores y stock de seguridad.

El enfoque es de **predicción numérica (regresión)**, con variable objetivo `target_next_month_units`. Las alternativas supervisadas estudiadas son Ridge y Random Forest Regressor. El modelo finalmente seleccionado para la **funcionalidad de previsión** es una referencia estadística sencilla: **media de los últimos tres meses conocidos**. La selección no presupone que una técnica de aprendizaje automático deba imponerse a un baseline.

### Alcance y procedencia

La Entrega 02 describe siete CSV de una **muestra parcial cedida por un taller de Lorca (Región de Murcia)**, cuyo nombre comercial se mantiene confidencial. Según la autorización comunicada en esa entrega, la **muestra cedida puede utilizarse y publicarse** siempre que no se revele el nombre del negocio ni datos privados o que permitan identificar al establecimiento, clientes o vehículos; no se dispone del histórico completo. Este documento no identifica al taller y hace referencia exclusivamente a la muestra disponible, sin inferir representatividad de otros negocios.

## 2. Datos de entrada y salida

### Dataset Gold y granularidad

La fuente directa del experimento es `tallerpredict/datos/processed/gold_consumo_mensual_repuestos.csv` (ruta relativa a la raíz del repositorio).

El Gold fue generado por `tallerpredict/scripts/etapa_2/preparar_datos.py` a partir de los siete CSV de `tallerpredict/datos/`. Cada fila representa una combinación **repuesto × mes de referencia**. Sus 2.640 filas incluyen **80 repuestos**, **33 meses de referencia** (marzo de 2021–noviembre de 2023) y **14 columnas**. Los objetivos cubren abril de 2021–diciembre de 2023. El análisis exploratorio registró **0 nulos, 0 duplicados repuesto-mes, 0 combinaciones mensuales ausentes** y **66,21 % de objetivos iguales a cero**. Estos controles verifican consistencia estructural, no garantizan ausencia de sesgos u omisiones en los registros originales.

Existen cinco unidades de medida: `ud`, `l`, `kit`, `juego` y `kg`. No es correcto sumar los errores físicos de estas categorías como si representaran una misma magnitud.

### Variable objetivo y entradas

| Papel | Columna | Interpretación y disponibilidad |
|---|---|---|
| Objetivo | `target_next_month_units` | Consumo **del mes siguiente**; desconocido en el momento de predicción. |
| Identificación categórica | `part_id` | Repuesto, conocido al momento de predicción; se codifica mediante `OneHotEncoder` en Ridge y Random Forest. |
| Entrada histórica | `lag_1_units` | **Consumo del propio mes de referencia**. En el código de preparación se obtiene con `shift(0)`. |
| Entrada histórica | `lag_2_units` | Consumo del mes anterior al de referencia. |
| Entrada histórica | `lag_3_units` | Consumo de dos meses antes del de referencia. |
| Entrada histórica | `rolling_3_units` | Media de esos tres meses, incluido el mes de referencia. |
| Entrada calendárica derivada | `target_calendar_month` | Mes calendario que se predice, calculado como `month_date` + 1 mes; es información conocida. |

Las variables de contexto `part_name`, `part_code` y `unit` se mantienen para **identificar, presentar y analizar** los resultados, pero no se utilizan como entradas independientes de los modelos. `unit_cost` y `supplier_lead_days` tampoco se usan en este experimento: su historización y su pertinencia operativa requieren estudio posterior.

**Prevención de fugas de información (*data leakage*):** se pronostica al **cierre** del mes de referencia, momento en el que ya es conocido `lag_1_units`; el objetivo del siguiente mes **no** figura en las entradas. Ridge usa un `Pipeline` con `OneHotEncoder` y `StandardScaler`, y Random Forest un `Pipeline` con `OneHotEncoder`; los transformadores se ajustan exclusivamente con el entrenamiento de cada ventana. Las escalas del error por repuesto también se calculan usando únicamente las etiquetas de entrenamiento de esa ventana.

**Riesgos de calidad y sesgo:** los ceros representan ausencia de **consumo registrado**, no necesariamente ausencia de demanda (puede haber roturas de stock o reparaciones no efectuadas). La muestra procede de un único taller y es parcial. La estacionalidad puede no generalizarse. Los repuestos con pocas observaciones positivas y las diferencias entre unidades generan incertidumbre. Las predicciones negativas de regresores se recortan a cero.

## 3. Baseline y selección de modelos

Se evaluaron cinco alternativas sobre las mismas particiones temporales:

| Método | Predicción | Motivo de inclusión |
|---|---|---|
| `siempre_cero` | 0 | Referencia mínima dada la gran proporción de meses sin consumo. |
| `ultimo_mes` | `lag_1_units` | Persistencia del último valor conocido. |
| `media_tres_meses` | `rolling_3_units` | Suavizado de los tres meses conocidos; previsión interpretable. |
| `ridge` | Regresión lineal regularizada, `alpha=10` | Primera alternativa supervisada interpretable. |
| `random_forest` | 300 árboles, profundidad máxima 12, mínimo 3 muestras por hoja, `random_state=42` | Alternativa supervisada no lineal. |

No se ajustaron hiperparámetros usando el test. Los parámetros de Ridge y Random Forest corresponden a los experimentos de desarrollo conservados en el repositorio.

### Primera validación (junio–agosto de 2023 como meses de referencia)

| Método | MAE escalado macro por repuesto ↓ |
|---|---:|
| Siempre cero | 0,271496 |
| Último mes | 0,389234 |
| Media de tres meses | 0,348034 |
| Ridge | 0,401014 |
| Random Forest | 0,314984 |

En esa ventana aislada, «siempre cero» obtuvo el menor MAE escalado. Sin embargo, ese resultado debía interpretarse con cautela: **73,75 % de objetivos eran cero** y dicha referencia no anticipa ningún consumo positivo.

### Comparación mediante cuatro ventanas crecientes

| Método | MAE escalado macro por repuesto ↓ |
|---|---:|
| **Media de tres meses** | **0,397123** |
| Random Forest | 0,424934 |
| Siempre cero | 0,439826 |
| Ridge | 0,444599 |
| Último mes | 0,467206 |

La media móvil obtuvo el menor error escalado agregado en **cuatro ventanas** y se seleccionó antes de abrir el test. Random Forest quedó como alternativa de ML secundaria, no como nueva candidata seleccionable después de la prueba.

Fuentes internas de resultados: `tallerpredict/resultados/ml/baselines/`, `primer_modelo/`, `random_forest/` y `validacion_temporal/`.

## 4. Validación y evaluación

### Diseño de las particiones

| Uso | Meses de referencia | Registros |
|---|---|---:|
| Entrenamiento inicial | Mar. 2021–May. 2023 | 2.160 |
| Validación inicial | Jun.–Ago. 2023 | 240 |
| Prueba final reservada | Sep.–Nov. 2023 | 240 |

Para la evaluación final, el modelo supervisado secundario se reajustó con **2.400 filas anteriores al test** (marzo de 2021–agosto de 2023), sin cambiar sus hiperparámetros. La media móvil no requiere ajuste. Las etiquetas de prueba corresponden a **octubre–diciembre de 2023**.

Las ventanas de validación creciente, siempre anteriores al test, fueron:

| Ventana | Entrenamiento hasta | Validación (meses de referencia) | Filas entrenamiento / validación |
|---|---|---|---:|
| V1 | Ago. 2022 | Sep.–Nov. 2022 | 1.440 / 240 |
| V2 | Nov. 2022 | Dic. 2022–Feb. 2023 | 1.680 / 240 |
| V3 | Feb. 2023 | Mar.–May. 2023 | 1.920 / 240 |
| V4 | May. 2023 | Jun.–Ago. 2023 | 2.160 / 240 |

En total se compararon **960 observaciones de validación por método**, antes de abrir el conjunto final. El script y los CSV de auditoría registran estos cortes.

### Métrica principal y precauciones

El criterio principal es el **MAE escalado macro por repuesto**. Para cada repuesto se calcula el promedio de `|real − predicho| / max(media del objetivo del repuesto en entrenamiento, 1)`; posteriormente se promedia el resultado de los repuestos. En cada ventana y en la prueba se usan únicamente las escalas obtenidas con su entrenamiento. Es una **normalización pragmática para comparar escalas**, no una medición económica ni una equivalencia física entre litros, kilos y unidades.

Se complementa con: MAE escalado en registros con consumo positivo, MAE y sesgo por **unidad de medida** y revisión de errores grandes. El análisis de umbrales 0, 0,5 y 1 de la validación fue **exploratorio**, no una regla de compra ni un clasificador operativo.

### Protocolo congelado y resultado final

Antes de acceder al test quedó registrado el protocolo en:

`tallerpredict/resultados/ml/protocolo_final/protocolo_paso7.json`

Se fijó como candidata `media_tres_meses`; referencia `siempre_cero`; alternativa secundaria `random_forest`; y umbral de aceptación **reducción del MAE escalado macro ≥ 5 % respecto a siempre cero**. Ese 5 % fue un criterio operativo de estudio, **no un requisito del máster ni un umbral validado por el taller**.

| Método | MAE escalado macro en test ↓ | MAE escalado macro en positivos ↓ | Observaciones de test |
|---|---:|---:|---:|
| Siempre cero | 0,701927 | 1,688072 | 240 |
| **Media de tres meses** | **0,501480** | 1,092188 | 240 |
| Random Forest | 0,506915 | **0,933911** | 240 |

La mejora de la candidata principal respecto a predecir cero fue del **28,56 %**, por lo que **cumple** el criterio previamente establecido. Los 240 casos incluyen **103 consumos positivos y 137 consumos cero**. Random Forest tuvo menor error en los casos positivos, pero no desplazó a la solución elegida antes de conocer el test.

El archivo `tallerpredict/resultados/ml/evaluacion_final/decision_test.json` conserva la decisión; `metricas_test.csv`, `metricas_test_por_unidad.csv` y `predicciones_test.csv` permiten contrastarla.

### Errores y limitaciones relevantes

En test la media móvil obtuvo MAE de **0,694 `ud`**, **3,063 `l`**, **1,444 `kg`**, **0,917 `kit`** y **2,148 `juego`**, calculados **por separado**. Los grupos de menor tamaño son menos estables (solo **3 observaciones `kg`** en test). El modelo puede infraestimar repuntes repentinos tras varios meses de consumo bajo; también puede sobreestimar repuestos que dejan de consumirse. No se dispone de evidencia causal ni de una evaluación de ahorro, roturas de stock o reducción de espera de vehículos. Tres meses de test ofrecen evidencia limitada de generalización temporal.

En consecuencia, el criterio estadístico fijado se considera cumplido, **pero no equivale a validar decisiones de reposición automáticas**.

## 5. Decisión y uso en el producto

### Solución elegida y motivo

Se adopta **`media_tres_meses`** para la primera previsión del MVP: es transparente, puede explicarse al responsable del taller y fue la mejor según la métrica principal agregada en las cuatro ventanas de validación; en test mantuvo el criterio de aceptación previamente definido. El experimento de Ridge y Random Forest se conserva como contraste de alternativas de Machine Learning, sin forzar una conclusión favorable a modelos complejos.

**Suficiencia para el MVP:** suficiente **solo como funcionalidad orientativa de estimación mensual** sujeta a supervisión humana. No es evidencia suficiente para calcular compras definitivas ni automatizar pedidos, porque faltan existencias vigentes, pedidos pendientes, costes del error y límites de riesgo operativo.

### Salida propuesta para el frontal (contrato conceptual, no API implementada)

Ejemplo **ilustrativo**, sin afirmar que corresponda a un registro real ni que la interfaz esté ya desplegada:

```json
{
  "part_id": 12,
  "part_code": "EJEMPLO-12",
  "target_month": "2024-01",
  "unit": "ud",
  "predicted_consumption": 2.3,
  "method": "media_tres_meses",
  "interpretation": "Estimación orientativa; revisar el stock real antes de comprar"
}
```

La aplicación debería presentar también el nombre de la pieza y su unidad, indicar el horizonte temporal y la fecha de actualización, mostrar las limitaciones de la previsión y **no confundir cifras continuas/fraccionarias con una cantidad de compra redondeada**. En esta entrega **no se ha desplegado el modelo ni el frontal**; la siguiente etapa de UX se mantiene separada.

## Reproducibilidad y evidencias en el repositorio actual

> **Directorio de trabajo:** situarse en `tallerpredict/`, donde están `datos/`, `scripts/`, `requirements-ml.txt` y `resultados/`. Los scripts usan `Path(__file__).resolve().parents[2]`, que funciona con la organización actual `scripts/etapa_3/`.

### Instalación

El repositorio declara Python **3.12.10** en `.python-version`. Sus dependencias están en `tallerpredict/requirements-ml.txt`, que **ya incluye Matplotlib** además de pandas, NumPy y scikit-learn y referencia `requirements.txt`. Instalar las versiones declaradas en un entorno virtual compatible:

```powershell
# Situados en tallerpredict/
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-ml.txt
```

### Orden de ejecución desde `tallerpredict/`

```powershell
# Preparación de datos de la Entrega 02 (solo si se quieren regenerar Silver y Gold)
python scripts/etapa_2/preparar_datos.py

# Entrega 03: experimentos y validación
python scripts/etapa_3/analisis_exploratorio_gold.py
python scripts/etapa_3/preparar_experimento_ml.py
python scripts/etapa_3/evaluar_baselines.py
python scripts/etapa_3/entrenar_primer_modelo.py
python scripts/etapa_3/entrenar_random_forest.py
python scripts/etapa_3/validar_modelos_temporal.py

# Verificar el protocolo predefinido SIN volver a evaluar test
python scripts/etapa_3/preparar_evaluacion_final.py

# Ejecutar la evaluación final
python scripts/etapa_3/preparar_evaluacion_final.py --ejecutar-evaluacion-final
```

**No volver a ejecutar** `--ejecutar-evaluacion-final`: el test **ya fue abierto en el Paso 8** y sus métricas se han registrado. El propio script impide sobrescribir `metricas_test.csv`. Conservar el protocolo y los resultados finales originales como evidencia de la decisión previa al test.

Las salidas de ML están bajo `tallerpredict/resultados/ml/` en los subdirectorios `eda/`, `diseno_experimento/`, `baselines/`, `primer_modelo/`, `random_forest/`, `validacion_temporal/`, `protocolo_final/` y `evaluacion_final/`.

### Privacidad, divulgación y límites de reproducibilidad

Este repositorio recibido incluye los CSV originales y el Gold; **no deben difundirse sin revisar** que la muestra publicada cumple exactamente las condiciones de autorización y que no contiene identificadores privados. El paquete de actualización del Paso 9 **no redistribuye** esos CSV ni los resultados fila a fila. Los resultados pueden reproducirse localmente con los datos que ya tiene el titular del proyecto. PostgreSQL 18 y los SQL del repositorio siguen disponibles para la fase de datos, pero **los scripts de ML leen CSV locales y no necesitan una conexión a PostgreSQL**.

### Trazabilidad de evidencias

- **Entrega 02 y contexto del origen:** `docs/entregas/02_datos_y_preparacion.md`.
- **Calidad del Gold:** `tallerpredict/datos/processed/reporte_calidad.json`; EDA: `tallerpredict/resultados/ml/eda/resumen_eda.json`.
- **Particiones:** `tallerpredict/resultados/ml/diseno_experimento/configuracion_experimento.json`.
- **Validación temporal:** `tallerpredict/resultados/ml/validacion_temporal/metricas_globales_ventanas.csv` y `auditoria_ventanas.csv`.
- **Protocolo congelado:** `tallerpredict/resultados/ml/protocolo_final/protocolo_paso7.json`.
- **Test y decisión:** `tallerpredict/resultados/ml/evaluacion_final/metricas_test.csv` y `decision_test.json`.

**Criterio de cierre:** otra persona puede comprender qué se ha previsto, cuáles han sido las entradas y el objetivo, cómo se eligió y comparó la solución, qué errores presenta y qué uso —limitado— tendrá su predicción en el MVP.
