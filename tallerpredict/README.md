# TallerPredict V0.3 — aplicación local para Windows (prototipo)

**Alcance**: PostgreSQL local + interfaz web **solo en este ordenador** + consulta de vehículos/órdenes/inventario + importación CSV + estimador orientativo de reposición. Se ha conservado el esquema y el generador sintético de la fase anterior.

**No es aún un instalador Windows, ni una herramienta lista para producción.** Requiere Python, Docker Desktop (o PostgreSQL 16 configurado por separado) y ejecución de comandos la primera vez. No incluye autenticación, histórico de pedidos en tránsito, panel de edición de reparaciones, ni modelo de ML validado. No publicar el puerto 8000 a internet. Mantenerlo en `127.0.0.1`.

## Instalación (Windows / PowerShell)

1. Instala Python 3.11+ y Docker Desktop (o PostgreSQL 16) en el ordenador.
2. Descomprime la carpeta. Abre PowerShell dentro de ella.
3. Inicia PostgreSQL: `docker compose up -d db`. Espera hasta que esté listo: `docker compose ps`.
4. Inicializa el esquema **una sola vez**:
   `Get-Content sql/001_schema.sql | docker compose exec -T db psql -U tallerpredict -d tallerpredict -v ON_ERROR_STOP=1`
5. Crea el entorno Python y dependencias:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   Si PowerShell impide activar scripts, puedes utilizar `.venv\Scripts\python.exe` directamente en los siguientes comandos.
6. Importa los datos simulados (desde la raíz del proyecto):
   ```powershell
   python -m src.import_csv --reparaciones datos/reparaciones.csv --adquisiciones datos/adquisiciones.csv
   ```
7. Arranca la interfaz:
   ```powershell
   python -m uvicorn src.app:app --host 127.0.0.1 --port 8000
   ```
8. Abre http://127.0.0.1:8000 en el navegador. En siguientes ocasiones puedes usar `start_windows.bat` tras iniciar PostgreSQL.

**Usuarios sin Docker:** crea usuario, base y ejecuta `sql/001_schema.sql` en PostgreSQL. Define la variable de entorno `DATABASE_URL` con cadena `postgresql://usuario:clave@localhost:5432/basedatos` antes de lanzar Python.

## Uso de la interfaz

- **Resumen**: recuentos y últimas órdenes de entrada.
- **Vehículos**: búsqueda por identificador/marca/modelo (hasta 150 resultados).
- **Órdenes**: últimas 150 entradas con número de reparaciones y piezas diferentes.
- **Inventario**: existencias por referencia a partir de movimientos, sin maquillado de saldos negativos.
- **Recomendaciones**: línea base determinista basada en consumo agregado de 6 meses con 30 días/mes y margen de 7 días. Solo como demostración; no incluye estacionalidad, compatibilidad, incertidumbre, pedidos en tránsito ni ajuste del nivel de servicio.
- **Importación**: carga **ambos CSV a la vez**, con validación de columnas, una transacción SQL y claves idempotentes para no duplicar consumos en sucesivas cargas. Cada CSV admite hasta 12 MB.

El importador exige los nombres de las columnas de `datos/reparaciones.csv` y `datos/adquisiciones.csv`. La fecha de entrada/salida/reparación usa `dd/mm/yyyy hh:mm` y la de adquisición `dd/mm/yyyy`. Ambos CSV se leen en UTF-8, con delimitador coma. Los identificadores `id_orden`, `id_reparacion`, `codigo_repuesto`, `id_movimiento` deben ser estables y únicos en su nivel correspondiente. No uses matrículas, nombres ni datos de clientes en las pruebas.

**Cautela de importación:** una repetición de los mismos archivos no duplica consumos, pero el importador no sobrescribe históricos corregidos: usa nuevas claves o un procedimiento controlado de corrección. Realiza una copia de seguridad antes de importar. No contiene aún un sistema de auditoría ni una etapa de conciliación de inventario, requisitos para el uso real.

## Estructura

- `sql/001_schema.sql`: siete tablas relacionadas, índices, vistas de stock y consumo mensual.
- `src/import_csv.py`: cargador transaccional de los dos archivos.
- `src/generate_demo.py` y `src/validate_data.py`: generador y comprobaciones de datos simulados.
- `src/app.py`: API/servidor web local FastAPI.
- `src/forecast.py`: heurística de referencia de stock.
- `src/templates/`, `src/static/`: interfaz web.
- `tests/test_forecast.py`: pruebas de la heurística.

## Validación y límites

Pruebas locales sin base de datos: `python -m pytest -q` (requiere pytest instalado). La conexión real, ejecución de `schema.sql` y la importación completa requieren PostgreSQL en ejecución. No deben darse por probadas hasta ejecutarlas en el equipo de destino. Los datos simulados contienen patrones artificiales y **no prueban precisión predictiva real**.

## Próximas fases

1. Configurador inicial y un instalador Windows que gestione el servicio PostgreSQL sin consola.
2. Importación asistida para CSV/Excel, detección de conflictos y mapeo de columnas de programas de taller.
3. Registro visual de movimientos y pedidos, con auditoría y backups.
4. Modelo ML con validación temporal y políticas de inventario sensibles a costes, plazos y demanda intermitente.

## Seguridad

La contraseña `cambiar_esta_clave` del `docker-compose.yml` **es solo para desarrollo**, cámbiala antes de cargar datos reales. La interfaz no tiene usuarios ni permisos; no la expongas en red. Para una versión comercial harán falta autenticación, autorizaciones, cifrado de backups y políticas de protección de datos.
