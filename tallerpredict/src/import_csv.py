"""Importación atómica e idempotente de las dos tablas CSV a PostgreSQL."""
import argparse,csv,os
from datetime import datetime
from decimal import Decimal,InvalidOperation
from pathlib import Path

DT='%d/%m/%Y %H:%M';D='%d/%m/%Y'
REQ_REP={'id_orden','id_vehiculo','marca','modelo','cilindrada','combustible','año_fabricacion','fecha_entrada','fecha_salida','id_reparacion','reparaciones','fecha_reparacion','repuesto_necesario','codigo_repuesto','cantidad_utilizada'}
REQ_STOCK={'id_movimiento','reparacion','repuesto','codigo_repuesto','cantidad','fecha_adquisicion','coste_unitario','plazo_entrega_dias'}
FUELS={'gasoil','gasolina','electrico','hibrido_gasolina','hibrido_gasoil'}

def parse_date(val,fmt,optional=False):
    if optional and not val.strip():return None
    return datetime.strptime(val.strip(),fmt)

def positive(value):
    d=Decimal(value.replace(',','.'))
    if not d.is_finite() or d<=0:raise ValueError('cantidad debe ser positiva')
    return d

def read_csv(path,required):
    with open(path,encoding='utf-8-sig',newline='') as f:
        rd=csv.DictReader(f,delimiter=';') if Path(path).suffix.lower()=='.semicolon' else csv.DictReader(f)
        missing=required-set(rd.fieldnames or ())
        if missing:raise ValueError(f'{path}: faltan columnas: {sorted(missing)}')
        for num,row in enumerate(rd,2):
            if not any(v and v.strip() for v in row.values() if isinstance(v,str)):continue
            yield num,{k:(v or '').strip() for k,v in row.items()}

def one(cur,sql,params):
    cur.execute(sql,params);return cur.fetchone()[0]

def import_all(conn,repairs_path,acquisitions_path):
    counts={'reparaciones_filas':0,'adquisiciones_filas':0}
    with conn.transaction():
      with conn.cursor() as cur:
        for line,r in read_csv(acquisitions_path,REQ_STOCK):
          try:
            code=r['codigo_repuesto']; name=r['repuesto']; mid=r['id_movimiento']
            if not all((code,name,mid)):raise ValueError('referencia, nombre e id_movimiento obligatorios')
            qty=positive(r['cantidad']); cost=Decimal(r['coste_unitario'].replace(',','.'))
            if cost<0 or not cost.is_finite():raise ValueError('coste inválido')
            lead=int(r['plazo_entrega_dias']);assert lead>=0
            date=parse_date(r['fecha_adquisicion'],D)
            pid=one(cur,"INSERT INTO parts(part_code,name,unit_cost,supplier_lead_days) VALUES(%s,%s,%s,%s) ON CONFLICT(part_code) DO UPDATE SET name=EXCLUDED.name RETURNING id",(code,name,cost,lead))
            cur.execute("INSERT INTO inventory_movements(movement_key,part_id,movement_at,quantity_delta,movement_type) VALUES(%s,%s,%s,%s,'compra') ON CONFLICT(movement_key) DO NOTHING",(mid,pid,date,qty))
            counts['adquisiciones_filas']+=1
          except (ValueError,InvalidOperation,AssertionError,TypeError) as e:raise ValueError(f'{acquisitions_path}, línea {line}: {e}') from e
        for line,r in read_csv(repairs_path,REQ_REP):
          try:
            if not all(r[x] for x in ('id_orden','id_vehiculo','marca','modelo','combustible','id_reparacion','reparaciones','codigo_repuesto','repuesto_necesario')):raise ValueError('faltan identificadores o campos obligatorios')
            fuel=r['combustible'].lower()
            if fuel not in FUELS:raise ValueError('combustible no válido')
            year=int(r['año_fabricacion']);cc=int(r['cilindrada']) if r['cilindrada'] else None
            entry=parse_date(r['fecha_entrada'],DT);exit_=parse_date(r['fecha_salida'],DT,True);performed=parse_date(r['fecha_reparacion'],DT)
            if exit_ and exit_<entry:raise ValueError('salida anterior a entrada')
            if performed<entry or (exit_ and performed>exit_):raise ValueError('reparación fuera de estancia')
            qty=positive(r['cantidad_utilizada'])
            vid=one(cur,'INSERT INTO vehicles(vehicle_key,brand,model,displacement_cc,fuel,manufacture_year) VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(vehicle_key) DO UPDATE SET vehicle_key=EXCLUDED.vehicle_key RETURNING id',(r['id_vehiculo'],r['marca'],r['modelo'],cc,fuel,year))
            oid=one(cur,'INSERT INTO work_orders(order_key,vehicle_id,entry_at,exit_at) VALUES(%s,%s,%s,%s) ON CONFLICT(order_key) DO UPDATE SET order_key=EXCLUDED.order_key RETURNING id',(r['id_orden'],vid,entry,exit_))
            tid=one(cur,'INSERT INTO repair_types(name) VALUES(%s) ON CONFLICT(name) DO UPDATE SET name=EXCLUDED.name RETURNING id',(r['reparaciones'],))
            eid=one(cur,'INSERT INTO repair_events(repair_key,order_id,repair_type_id,performed_at) VALUES(%s,%s,%s,%s) ON CONFLICT(repair_key) DO UPDATE SET repair_key=EXCLUDED.repair_key RETURNING id',(r['id_reparacion'],oid,tid,performed))
            pid=one(cur,'INSERT INTO parts(part_code,name) VALUES(%s,%s) ON CONFLICT(part_code) DO UPDATE SET name=EXCLUDED.name RETURNING id',(r['codigo_repuesto'],r['repuesto_necesario']))
            cur.execute('INSERT INTO part_usage(repair_event_id,part_id,quantity) VALUES(%s,%s,%s) ON CONFLICT(repair_event_id,part_id) DO NOTHING',(eid,pid,qty))
            cur.execute("INSERT INTO inventory_movements(movement_key,part_id,movement_at,quantity_delta,movement_type,repair_event_id) VALUES(%s,%s,%s,%s,'consumo',%s) ON CONFLICT(movement_key) DO NOTHING",(f"U:{r['id_reparacion']}:{r['codigo_repuesto']}",pid,performed,-qty,eid))
            counts['reparaciones_filas']+=1
          except (ValueError,InvalidOperation,TypeError) as e:raise ValueError(f'{repairs_path}, línea {line}: {e}') from e
    return counts

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reparaciones',default='datos/reparaciones.csv');p.add_argument('--adquisiciones',default='datos/adquisiciones.csv')
    a=p.parse_args();dsn=os.environ.get('DATABASE_URL','postgresql://tallerpredict:cambiar_esta_clave@localhost:5432/tallerpredict')
    import psycopg
    with psycopg.connect(dsn) as c:print(import_all(c,a.reparaciones,a.adquisiciones))
