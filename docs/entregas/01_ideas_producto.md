# Propuesta de ideas iniciales de proyecto

---

# Idea 1 - SmartStock Auto: Optimización del stock de recambios mediante análisis de reparaciones

## Problema que resuelve

Actualmente, muchos talleres mecánicos gestionan el stock de piezas de recambio basándose principalmente en la experiencia de los mecánicos o en las reparaciones realizadas recientemente. Esto provoca que, en numerosas ocasiones, no se disponga de determinadas piezas cuando un vehículo necesita una reparación, obligando a solicitar el recambio al proveedor y aumentando el tiempo que el vehículo permanece inmovilizado.

Por otro lado, también es habitual almacenar piezas que apenas se utilizan, ocupando espacio y generando un coste económico innecesario.

Mediante el análisis histórico de todas las reparaciones realizadas en un taller, sería posible identificar:

- Los modelos de vehículos que más frecuentan el taller.
- Las averías más habituales de cada modelo.
- Las piezas que se sustituyen con mayor frecuencia.
- La relación entre determinadas averías y el kilometraje o la antigüedad del vehículo.

Toda esta información permitiría optimizar la gestión del inventario y anticipar qué piezas conviene mantener en stock.

La decisión concreta que se pretende mejorar mediante este proyecto sería:

> **¿Qué recambios debería mantener el taller en stock y en qué cantidad para reducir el tiempo de inmovilización de los vehículos sin aumentar innecesariamente el coste de inventario?**

El usuario principal de la solución sería el **responsable del taller o responsable de almacén**, que podría utilizar los resultados del análisis para planificar los pedidos y gestionar el inventario.

Este proyecto representa un caso de uso real dentro del ámbito empresarial, ya que persigue mejorar un proceso operativo del taller mediante el uso de datos históricos y análisis predictivo.

## Motivación para realizar el proyecto

Este proyecto resulta especialmente interesante porque combina análisis de datos con optimización de procesos empresariales.

Su aplicación podría generar un importante ahorro económico para talleres mecánicos al reducir tanto el exceso de inventario como los tiempos de espera de los clientes.

Desde el punto de vista técnico, permitiría aplicar conocimientos del máster relacionados con:

- Análisis exploratorio de datos (EDA).
- Machine Learning.
- Sistemas de recomendación.
- Predicción de demanda.
- Visualización mediante dashboards interactivos.

Además, es razonable pensar que un taller dispone de históricos de reparaciones, facturas, vehículos atendidos y piezas utilizadas, por lo que existirían datos suficientes para desarrollar el proyecto.

El proyecto podría realizarse inicialmente tomando como referencia los datos históricos de un único taller mecánico, lo que permitiría acotar mejor el problema y adaptar la solución a un caso de uso real.

## A quién impacta

El usuario principal sería:

- Responsable del taller.
- Responsable de almacén.

Los principales beneficiarios de la solución serían:

- Talleres mecánicos independientes.
- Redes de talleres.
- Concesionarios oficiales.
- Responsables de almacén.
- Jefes de taller.
- Clientes, que recibirían su vehículo reparado en menos tiempo.

## Por qué tiene valor

La solución aportaría valor porque permitiría:

- Mejorar la toma de decisiones sobre el inventario.
- Determinar qué recambios conviene mantener disponibles.
- Estimar las cantidades necesarias de determinadas piezas.
- Reducir costes de almacenamiento.
- Disminuir el tiempo de reparación de los vehículos.
- Detectar patrones de averías según marca y modelo.
- Mejorar la planificación de pedidos.
- Incrementar la satisfacción de los clientes.

---

# Idea 2 - AgroPredict Lorca: Predicción de necesidades de riego en explotaciones agrícolas

## Problema que resuelve

La agricultura en Lorca depende en gran medida de unos recursos hídricos limitados. Muchos agricultores planifican el riego basándose en la experiencia o en calendarios fijos, sin considerar conjuntamente variables como la meteorología, el tipo de cultivo, la humedad del suelo o el historial de consumo de agua.

Esto puede provocar un consumo excesivo de agua o un riego insuficiente que afecte a la producción.

Mediante el análisis de datos meteorológicos, sensores de humedad y necesidades hídricas del cultivo, sería posible estimar cuándo y cuánto regar una parcela.

La decisión concreta que se pretende mejorar mediante este proyecto sería:

> **¿Cuándo debería realizarse el próximo riego y qué cantidad de agua debería aplicarse para mantener unas condiciones adecuadas de humedad del cultivo minimizando el consumo de agua?**

El usuario principal de la solución sería el **agricultor o técnico responsable de la explotación**, que podría utilizar la información generada para planificar el riego.

Para evitar que el proyecto abarque demasiadas variables o funcionalidades, se podría acotar inicialmente a **un determinado cultivo y tipo de explotación agrícola de la zona de Lorca**. Como podría ser el cultivo de brócoli en una explotación de regadío intensivo.

No se trata únicamente de realizar predicciones, sino de ayudar a los agricultores a tomar mejores decisiones relacionadas específicamente con la gestión del agua en un contexto de recursos hídricos limitados.

## Motivación para realizar el proyecto

La Región de Murcia es una de las zonas agrícolas más importantes de España y, al mismo tiempo, una de las más afectadas por la sequía.

Este proyecto permitiría aplicar técnicas de Machine Learning, análisis temporal y visualización de datos en un problema con una elevada relevancia económica y ambiental.

Existen numerosas fuentes de datos públicas (AEMET, SIAM, Confederación Hidrográfica del Segura, etc.) que podrían hacer viable el proyecto.

Además, el proyecto permitiría trabajar con datos relacionados con:

- Condiciones meteorológicas.
- Humedad del suelo.
- Características del cultivo.
- Historial de riego.
- Necesidades hídricas.
- Consumo de agua.

El objetivo principal sería mantener el foco en la **optimización del riego**, evitando ampliar inicialmente el proyecto hacia otras decisiones relacionadas con la producción agrícola.

## A quién impacta

El usuario principal sería:

- Agricultor.
- Técnico responsable de la explotación.

Los principales beneficiarios serían:

- Agricultores.
- Cooperativas agrícolas.
- Comunidades de regantes.
- Administraciones públicas.

## Por qué tiene valor

La solución aportaría valor ya que permitiría:

- Reducir el consumo de agua.
- Mejorar la planificación del riego.
- Evitar riegos innecesarios.
- Reducir el riesgo de un riego insuficiente.
- Disminuir costes asociados al consumo de agua.
- Mejorar la gestión de los recursos hídricos.
- Favorecer una agricultura más sostenible.

---

# Idea 3 - AgroYield Murcia: Predicción de la producción agrícola mediante datos climáticos y de cultivo

## Problema que resuelve

Los agricultores necesitan estimar con la mayor precisión posible la producción que obtendrán al finalizar cada campaña. Sin embargo, factores como la meteorología, el tipo de suelo, la variedad cultivada, la disponibilidad de agua o las fechas de siembra hacen que esta estimación resulte complicada.

La falta de previsiones fiables dificulta la planificación de la mano de obra, la contratación del transporte, la negociación con compradores y la gestión de los recursos disponibles.

El proyecto propone analizar datos históricos de campañas agrícolas para desarrollar un modelo capaz de estimar el rendimiento esperado de un cultivo antes de su recolección.

La decisión concreta que se pretende mejorar mediante este proyecto sería:

> **¿Cuál será el rendimiento esperado de una determinada parcela antes de la recolección para poder planificar los recursos, la logística y la comercialización de la producción?**

El usuario principal de la solución sería el **responsable de producción de una explotación agrícola o de una cooperativa**, que podría utilizar la predicción para planificar la campaña.

Para diferenciar esta propuesta de AgroPredict Lorca, el proyecto se centraría exclusivamente en la **predicción del rendimiento o producción agrícola**, dejando fuera la decisión sobre cuándo y cuánto regar.

Además, el proyecto podría acotarse inicialmente a **un único cultivo o grupo reducido de cultivos**, evitando que el número de variables y casuísticas haga crecer excesivamente el alcance. Como podría ser el cultivo de brócoli y colifror.

No se trata únicamente de realizar una predicción estadística, sino de proporcionar una herramienta que facilite la planificación económica y logística de las explotaciones agrícolas.

## Motivación para realizar el proyecto

La Región de Murcia es una de las principales zonas productoras y exportadoras de frutas y hortalizas de Europa. Una predicción fiable de la producción permitiría optimizar numerosos procesos de la cadena agrícola.

Este proyecto permitiría aplicar conocimientos del máster relacionados con:

- Machine Learning para regresión.
- Análisis de datos climáticos.
- Integración de datos geográficos y satelitales.
- Series temporales.
- Visualización mediante cuadros de mando.

Los datos podrían obtenerse de explotaciones agrícolas, cooperativas, AEMET, SIAM, imágenes Sentinel-2 y registros históricos de producción.

El proyecto se centraría principalmente en estudiar cómo las características del cultivo y las condiciones experimentadas durante la campaña pueden utilizarse para estimar el rendimiento final.

## A quién impacta

El usuario principal sería:

- Responsable de producción de una explotación agrícola.
- Responsable de producción de una cooperativa.

La solución beneficiaría principalmente a:

- Agricultores.
- Cooperativas agrícolas.
- Empresas comercializadoras.
- Exportadores hortofrutícolas.
- Técnicos agrícolas.
- Empresas de logística.

## Por qué tiene valor

La herramienta aportaría valor porque permitiría:

- Mejorar la planificación de las campañas agrícolas.
- Estimar anticipadamente la producción esperada.
- Optimizar la contratación de personal.
- Facilitar la organización del transporte y almacenamiento.
- Anticipar posibles reducciones de producción.
- Apoyar la toma de decisiones comerciales.
- Reducir costes asociados a una mala planificación.

---

## Diferenciación de las propuestas agrícolas

Aunque las dos propuestas están relacionadas con la agricultura, abordan decisiones diferentes:

- **AgroPredict Lorca** se centra en la **gestión del agua**: cuándo y cuánto regar.
- **AgroYield Murcia** se centra en la **previsión de producción**: cuánto se espera cosechar.

De esta forma, ambas propuestas mantienen una relación con la agricultura de la Región de Murcia, pero presentan problemas, usuarios y decisiones diferentes.