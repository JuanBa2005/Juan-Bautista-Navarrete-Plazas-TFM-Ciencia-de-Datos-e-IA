"""TallerPredict: interfaz local de lectura, importación y previsión inicial."""
import os
import tempfile
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.import_csv import REQ_REP, REQ_STOCK, import_all, read_csv
from src.forecast import recommend, months_ago

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=select_autoescape(['html']))
app = FastAPI(title='TallerPredict Local', version='0.3.0', docs_url=None, redoc_url=None)
app.mount('/static', StaticFiles(directory=Path(__file__).parent / 'static'), name='static')

@contextmanager
def db():
    import psycopg
    from psycopg.rows import dict_row
    dsn=os.environ.get('DATABASE_URL','postgresql://tallerpredict:cambiar_esta_clave@localhost:5432/tallerpredict')
    with psycopg.connect(dsn, row_factory=dict_row, connect_timeout=4) as conn:
        yield conn

def render(name, **kwargs):
    return HTMLResponse(TEMPLATES.get_template(name).render(**kwargs))

def fetch(sql, params=()):
    with db() as conn:
        return conn.execute(sql, params).fetchall()

@app.get('/',response_class=HTMLResponse)
def home():
    try:
        stats = fetch("""SELECT (SELECT count(*) FROM vehicles) AS vehicles,
            (SELECT count(*) FROM work_orders) AS orders,
            (SELECT count(*) FROM parts) AS parts,
            (SELECT COALESCE(sum(units),0) FROM current_stock) AS units""")[0]
        recent = fetch("""SELECT w.order_key,v.brand,v.model,w.entry_at,w.exit_at
         FROM work_orders w JOIN vehicles v ON v.id=w.vehicle_id ORDER BY w.entry_at DESC LIMIT 10""")
        return render('dashboard.html', page='dashboard',stats=stats,recent=recent, error=None)
    except Exception as exc:
        return HTMLResponse(TEMPLATES.get_template('dashboard.html').render(page='dashboard',stats=None,recent=[],error='No hay conexión con PostgreSQL o no se ha inicializado el esquema. Revisa las instrucciones de instalación.'), status_code=503)

@app.get('/vehiculos', response_class=HTMLResponse)
def vehicles(q: str = ''):
    q=q.strip()[:80]
    rows=fetch("""SELECT v.vehicle_key,v.brand,v.model,v.displacement_cc,v.fuel,v.manufacture_year,
       (SELECT COUNT(*) FROM work_orders w WHERE w.vehicle_id=v.id) AS visits
       FROM vehicles v WHERE %s='' OR v.brand ILIKE %s OR v.model ILIKE %s OR v.vehicle_key ILIKE %s
       ORDER BY v.brand,v.model LIMIT 150""",(q,f'%{q}%',f'%{q}%',f'%{q}%'))
    return render('vehicles.html',page='vehicles',rows=rows,q=q)

@app.get('/ordenes', response_class=HTMLResponse)
def orders():
    rows=fetch("""SELECT w.order_key,v.brand,v.model,w.entry_at,w.exit_at,
      count(DISTINCT e.id) AS repairs,count(DISTINCT u.part_id) AS part_types
      FROM work_orders w JOIN vehicles v ON v.id=w.vehicle_id
      LEFT JOIN repair_events e ON e.order_id=w.id LEFT JOIN part_usage u ON u.repair_event_id=e.id
      GROUP BY w.id,v.brand,v.model ORDER BY w.entry_at DESC LIMIT 150""")
    return render('orders.html',page='orders',rows=rows)

@app.get('/inventario', response_class=HTMLResponse)
def stock():
    rows=fetch("""SELECT p.part_code,p.name,p.unit,p.unit_cost,p.supplier_lead_days,s.units,
      COALESCE((SELECT sum(u.quantity) FROM part_usage u JOIN repair_events e ON e.id=u.repair_event_id
       WHERE u.part_id=p.id AND e.performed_at >= (CURRENT_DATE-INTERVAL '90 days')),0) AS used_90d
      FROM parts p JOIN current_stock s ON s.part_id=p.id ORDER BY p.name""")
    return render('stock.html',page='stock',rows=rows)

@app.get('/recomendaciones', response_class=HTMLResponse)
def forecast():
    as_of = date.today()
    start=months_ago(as_of,6)
    rows=fetch("""SELECT p.part_code,p.name,p.supplier_lead_days,p.unit_cost,s.units,
      COALESCE(SUM(CASE WHEN e.performed_at >= %s AND e.performed_at < %s THEN u.quantity ELSE 0 END),0) AS used_6months
      FROM parts p JOIN current_stock s ON s.part_id=p.id
      LEFT JOIN part_usage u ON u.part_id=p.id LEFT JOIN repair_events e ON e.id=u.repair_event_id
      GROUP BY p.id,s.units ORDER BY p.name""",(start,as_of))
    suggestions=[dict(r,**recommend(r['used_6months'],r['units'],r['supplier_lead_days'])) for r in rows]
    return render('forecast.html',page='forecast',rows=suggestions,start=start,as_of=as_of)

@app.get('/importar',response_class=HTMLResponse)
def import_page():
    return render('import.html',page='import',message=None,error=None)

@app.post('/importar', response_class=HTMLResponse)
async def import_files(reparaciones: UploadFile = File(...), adquisiciones: UploadFile = File(...)):
    MAX_BYTES=12*1024*1024
    paths=[]
    try:
        for file,required in [(reparaciones,REQ_REP),(adquisiciones,REQ_STOCK)]:
            if not (file.filename or '').lower().endswith('.csv'):
                raise ValueError('Solo se admiten archivos CSV.')
            content=await file.read(MAX_BYTES+1)
            if len(content)>MAX_BYTES: raise ValueError('Cada CSV debe ocupar como máximo 12 MB.')
            with tempfile.NamedTemporaryFile(mode='wb',suffix='.csv',delete=False) as temp:
                temp.write(content);paths.append(temp.name)
            # Valida columnas, codificación y filas antes de escribir en DB
            for _line,_row in read_csv(paths[-1],required): pass
        with db() as conn:
            result=import_all(conn, paths[0], paths[1])
        return render('import.html',page='import',message=f"Importación realizada: {result['reparaciones_filas']} filas de reparaciones y {result['adquisiciones_filas']} de adquisiciones procesadas.",error=None)
    except (ValueError,UnicodeError) as exc:
        return HTMLResponse(TEMPLATES.get_template('import.html').render(page='import',message=None,error=str(exc)),status_code=400)
    except Exception:
        return HTMLResponse(TEMPLATES.get_template('import.html').render(page='import',message=None,error='No se pudo importar. Comprueba que PostgreSQL funciona y que los datos son consistentes. No se ha confirmado una importación parcial.'),status_code=500)
    finally:
        for path in paths:
            Path(path).unlink(missing_ok=True)

@app.get('/api/resumen')
def api_summary():
    return fetch("""SELECT (SELECT COUNT(*) FROM vehicles) vehicles,(SELECT COUNT(*) FROM work_orders) orders,(SELECT COUNT(*) FROM parts) parts""")[0]
