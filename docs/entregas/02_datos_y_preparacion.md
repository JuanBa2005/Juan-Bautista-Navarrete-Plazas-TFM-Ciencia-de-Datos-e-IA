# Proyecto final — Entrega 02: Datos y preparación

**Producto:** TallerPredict  
**Objetivo de esta entrega:** preparar un dataset trazable para explorar modelos que pronostiquen el **consumo de repuestos del mes siguiente**, sin entrenar modelos todavía.  
**Estado:** flujo local ejecutado sobre el ZIP proporcionado. **Procedencia declarada por la persona que aporta el proyecto:** registros operativos facilitados por un **taller mecánico de Lorca (Región de Murcia, España)**. El taller solicitó mantener confidencial su nombre comercial y compartió **solo una parte de sus registros por motivos de seguridad**. Esta declaración contextualiza la procedencia, pero no se acompaña de documentación de extracción, autorización de publicación o licencia; por ello no se presenta como verificación independiente ni como un conjunto completo de transacciones.

## 1. Qué datos necesita el producto

TallerPredict busca anticipar la cantidad de unidades de cada repuesto que necesitará un taller durante el **mes siguiente** para apoyar la planificación de compras y existencias. Una observación de **Gold** representa **un repuesto y un mes de referencia**; su variable objetivo es el número de unidades registradas como utilizadas en reparaciones **durante el mes siguiente**.

Son imprescindibles el catálogo de piezas (`parts`: identificador, unidad, coste y plazo de suministro), los consumos (`part_usage`: pieza y cantidad) y las fechas de reparación (`repair_events`: fecha y vínculo con consumo). El histórico del ZIP abarca de enero de 2021 a diciembre de 2023, con detalle de cada reparación. Se agrega a nivel mensual; se utilizan los tres meses anteriores o hasta el mes de referencia inclusive. Son deseables variables externas como estacionalidad de la demanda local, número de clientes, campañas, disponibilidad de proveedores y tiempos reales de entrega. Estas variables no están en el paquete y **no se inventan**.

La predicción se plantearía al **cierre del mes de referencia**, cuando ya se conoce el consumo de ese mes. En cada fila, `lag_1_units` es el consumo del mes de referencia, `lag_2_units` el del anterior, `lag_3_units` el de dos meses antes y `target_next_month_units` el del mes posterior. El conjunto preparado es una base para modelar, no una evaluación de precisión.

## 2. Fuentes reales y viabilidad

**Fuente de trabajo disponible:** los siete CSV entregados en el ZIP del proyecto `tallerpredict/datos/`, leídos directamente desde disco sin requerir conexión externa. El SQL proporcionado permite importar estos mismos archivos en PostgreSQL. El código de esta entrega realiza la preparación directamente en Python para hacerla reproducible sin instalar PostgreSQL.

| Archivo del ZIP | Registros | Finalidad |
|---|---:|---|
| `vehicles.csv` | 150 | Atributos de vehículos; contexto opcional |
| `repair_types.csv` | 25 | Catálogo de tipos de reparación |
| `parts.csv` | 80 | Catálogo de repuestos y atributos |
| `work_orders.csv` | 1.160 | Órdenes y vehículos asociados |
| `repair_events.csv` | 1.617 | Fecha de los trabajos realizados |
| `part_usage.csv` | 2.344 | Cantidad de piezas utilizada en cada reparación |
| `inventory_movements.csv` | 3.206 | Entradas, consumos, devoluciones y ajustes de almacén |

**Origen y acceso:** fuente primaria privada: exportación parcial de registros de un taller mecánico ubicado en Lorca, Región de Murcia, según información aportada por quien entrega el proyecto. El acceso consiste en los CSV cedidos para este trabajo; no hay API pública ni descarga abierta. Por petición del establecimiento no se revela su nombre comercial. **Cobertura:** los archivos contienen registros del período 2021–2023 y los eventos de reparación van del 5/01/2021 al 29/12/2023; **no representan necesariamente la totalidad de operaciones** porque el taller retuvo registros por seguridad. **Actualización:** es una instantánea de archivos, sin frecuencia declarada ni canal de actualización definido. **Estabilidad:** los CSV y el esquema SQL permiten reproducir esta ejecución, pero no hay compromiso documentado de nuevas extracciones ni garantía de continuidad. **Trazabilidad:** la procedencia se apoya en la declaración de quien aporta los archivos, no en una certificación o evidencia independiente de extracción.

**Alternativa si la fuente no está disponible:** acordar una nueva exportación minimizada y autorizada del software de gestión del mismo taller, o recurrir a otro establecimiento colaborador con un esquema equivalente (repuesto, cantidad y fecha). Si no se obtienen más datos, puede mantenerse el prototipo con la muestra parcial disponible, sin extrapolar sus resultados al total de actividad del taller.

## 3. Uso, privacidad y datos personales

Los registros proceden, según la información aportada, de un taller de Lorca que **no autoriza revelar su nombre comercial** y que **ha limitado la muestra compartida por motivos de seguridad**. El ZIP no incluye licencia ni autorización explícita para redistribuir datos. **Cesión de una muestra para realizar el trabajo no equivale a permiso para publicarla**, incluso si los CSV no llevan nombres de clientes. Se conservan localmente en `datos/` para reproducir el proceso, pero los archivos Bronze, Silver y Gold no deben subirse a repositorios públicos ni compartirse con terceros sin consentimiento específico del titular y revisión de privacidad. Para el repositorio público, publicar código, documentación y, solo si se permite, una muestra agregada o sintética sin riesgo de identificación; alternativamente, explicar el acceso privado y la ejecución local.

Los campos disponibles son fundamentalmente identificadores internos de vehículos, órdenes, piezas y reparaciones, sin nombres, teléfonos ni direcciones de clientes visibles en los CSV revisados. Las claves de vehículo y órdenes **podrían asociarse indirectamente a personas** en los sistemas del taller; se aplica minimización al evitar incorporarlas al Gold. El nombre comercial y otros datos identificativos del establecimiento tampoco se incorporan. No es necesario almacenar matrículas, nombres, teléfonos, direcciones ni identificadores personales para el pronóstico agregado. En explotación real se establecerían controles de acceso, retención limitada y revisión de riesgos de reidentificación, aplicando RGPD cuando corresponda.

## 4. Del dato bruto al dato utilizable: Bronze → Silver → Gold

### Bronze / Raw

Los **siete CSV originales** se mantienen sin modificar en `datos/*.csv`; el script los lee desde esa ubicación. Su estructura también está descrita en `sql/esquema_taller_postgresql.sql`. El fichero `validacion_datos_taller.json` incluido es información auxiliar de festivos y vacaciones: **no se incorpora al modelo** porque no es necesario para esta preparación. Los archivos CSV constituyen la **totalidad de la muestra recibida**, no la totalidad de registros del taller, y su procedencia se documenta mediante declaración de quien los ha aportado.

### Silver

El script `scripts/preparar_datos.py` genera `datos/processed/silver_*.csv` tras ejecutar estas comprobaciones y transformaciones:

1. Lectura de los siete CSV, conversión de fechas a tipos temporales y limpieza de espacios de cadenas.
2. Validación de identificadores `id` únicos y relaciones entre órdenes, reparaciones, piezas, consumos e inventario.
3. Verificación de cantidades usadas positivas, costes y plazos no negativos, y órdenes sin salida anterior a entrada.
4. Conservación de nulos esperados: **23** cilindradas de vehículos, **35** salidas abiertas de órdenes y **862** referencias a reparaciones no aplicables en movimientos; estos nulos no se imputan arbitrariamente.
5. Exportación de siete tablas Silver con columnas originales, tipos temporales normalizados y sin filas de identificación duplicada.

**Distinción relevante:** el producto utiliza `part_usage.quantity` para medir unidades consumidas, enlazadas con `repair_events.performed_at`. Los movimientos de almacén no se suman a esos usos: `inventory_movements.quantity_delta` incluye compras, devoluciones y ajustes y podría causar doble contabilización. No se construyen funciones predictoras a partir del inventario actual que pudieran revelar información futura.

### Gold

El script enlaza consumo de piezas con fecha de reparación, agrega la suma de cantidades por repuesto y mes y construye una rejilla completa de **80 repuestos × 36 meses** (enero 2021–diciembre 2023). Los meses sin eventos en la muestra se completan con `0` unidades **registradas en los datos cedidos**; dado que la extracción es parcial, estos ceros pueden corresponder a operaciones no compartidas y no demuestran ausencia de consumo o demanda real. Se calculan consumos contemporáneos e históricos conocidos al cierre del mes y el objetivo del mes siguiente. Se eliminan exclusivamente filas sin los tres meses de contexto o sin un mes posterior observable.

**Archivo final:** `datos/processed/gold_consumo_mensual_repuestos.csv`  
**Resultado verificado:** **2.640 observaciones**, **80 piezas**, **14 columnas**, **0 nulos**, meses de referencia desde **2021-03** hasta **2023-11**. La primera etiqueta corresponde al consumo de abril de 2021 y la última a diciembre de 2023.

| Campo Gold | Significado |
|---|---|
| `part_id`, `part_code`, `part_name` | Identificación de la pieza (sin datos personales) |
| `unit` | Unidad de medida (`ud`, `l`, etc.); no se deben mezclar unidades entre repuestos |
| `month_date` | Primer día del mes de referencia, etiqueta de período |
| `calendar_year`, `calendar_month` | Año y mes calendario de referencia |
| `unit_cost`, `supplier_lead_days` | Coste unitario y plazo del catálogo entregado; **solo atributos estáticos actuales, sin versiones históricas comprobadas** |
| `lag_1_units` | Unidades registradas en el mes de referencia |
| `lag_2_units` | Unidades registradas un mes antes |
| `lag_3_units` | Unidades registradas dos meses antes |
| `rolling_3_units` | Media de los tres consumos anteriores, incluyendo el mes de referencia |
| `target_next_month_units` | **Etiqueta a predecir:** consumo registrado durante el mes siguiente |

**Advertencia de modelado:** aunque el Gold no contiene consumo del mes objetivo entre las variables de entrada, los campos del catálogo de piezas no disponen de versionado temporal. Antes de entrenar modelos históricos deben comprobarse sus fechas de validez o excluirse. El conjunto no incluye información a escala de cliente ni eventos futuros, y no se ha realizado ninguna partición ni entrenamiento.

**Ejecución reproducible (desde la raíz del repositorio):**

```bash
python -m pip install -r requirements-data.txt
python scripts/preparar_datos.py
```

Tras ejecutarlo aparecen los archivos `datos/processed/silver_*.csv`, `datos/processed/gold_consumo_mensual_repuestos.csv` y `datos/processed/reporte_calidad.json`. El informe JSON resume cantidades, nulos y tamaño final. Si falta algún fichero, existe una clave externa huérfana o se incumple una regla validada, el proceso termina con un error explícito. No se necesita servidor PostgreSQL para este flujo. El SQL que ya estaba en el proyecto se mantiene sin modificaciones para quien prefiera consultar las tablas en PostgreSQL.

### Criterio de salida y verificación

El flujo fue ejecutado con éxito sobre los archivos proporcionados. Produce un único dataset tabular Gold con **una fila por pieza y mes**, variables históricas y etiqueta futura. El script valida automáticamente claves, ausencia de nulos y unicidad de la granularidad final. El resultado **es reproducible a partir del ZIP y no incluye un modelo entrenado**.

## 5. Riesgos y limitaciones

La procedencia se atribuye, por declaración de la persona que facilita el proyecto, a un taller real de Lorca, pero faltan pruebas independientes de extracción, permiso de redistribución y mecanismo de actualización. La muestra fue deliberadamente limitada por seguridad, por lo que puede presentar sesgos de selección y meses con ceros que no reflejen el consumo total. El histórico 2021–2023 y los costes y plazos estáticos pueden no representar la operativa actual. Si se pierde el acceso, se solicitarían nuevas exportaciones minimizadas y autorizadas o una fuente colaboradora alternativa. El Gold debe entenderse como un prototipo sobre datos parciales, no como medición exhaustiva de la demanda.
