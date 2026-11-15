"""Genera dos CSV sintéticos en español. No son datos reales de clientes."""
import argparse,csv,random,calendar
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path

CARS=[('Seat','Leon',1968,'gasoil'),('Seat','Ibiza',999,'gasolina'),('Volkswagen','Golf',1498,'gasolina'),('Renault','Clio',1461,'gasoil'),('Peugeot','308',1499,'gasoil'),('Toyota','Corolla',1798,'hibrido_gasolina'),('Hyundai','Tucson',1598,'hibrido_gasolina'),('Dacia','Sandero',999,'gasolina'),('Nissan','Leaf',None,'electrico'),('Ford','Focus',1499,'gasoil')]
REPAIRS={
 'cambio_aceite':[('ACEITE_5W30','Aceite 5W30',1),('FILTRO_ACEITE','Filtro de aceite universal demo',1)],
 'cambio_filtros':[('FILTRO_AIRE','Filtro de aire demo',1),('FILTRO_HAB','Filtro de habitáculo demo',1)],
 'cambio_frenos':[('PASTILLAS','Juego pastillas freno demo',1)],
 'cambio_bateria':[('BATERIA_70','Batería 70 Ah demo',1)],
 'refrigeracion':[('REFRIGERANTE','Refrigerante 5L demo',1),('TERMOSTATO','Termostato demo',1)],
 'neumaticos':[('NEUMATICO','Neumático demo',2)],
 'aire_acondicionado':[('FILTRO_HAB','Filtro de habitáculo demo',1),('GAS_AC','Carga de gas A/C demo',1)]}
FIELDS_REP=['id_orden','id_vehiculo','marca','modelo','cilindrada','combustible','año_fabricacion','fecha_entrada','fecha_salida','id_reparacion','reparaciones','fecha_reparacion','repuesto_necesario','codigo_repuesto','cantidad_utilizada']
FIELDS_STOCK=['id_movimiento','reparacion','repuesto','codigo_repuesto','cantidad','fecha_adquisicion','coste_unitario','plazo_entrega_dias']
DATE_FMT='%d/%m/%Y %H:%M'

def generate(output,seed=42,n=1100):
    rng=random.Random(seed); output=Path(output);output.mkdir(parents=True,exist_ok=True)
    vehicles=[(f'V{i:04d}',*rng.choice(CARS),rng.randint(2006,2025)) for i in range(1,241)]
    repairs=[];need=defaultdict(int)
    start=datetime(2023,1,1)
    end=datetime(2026,9,30,23,59)
    for i in range(1,n+1):
        veh=rng.choice(vehicles); vkey,brand,model,cc,fuel,year=veh
        day=start+timedelta(days=rng.randrange((end-start).days))
        valid_types=list(REPAIRS)
        if fuel=='electrico':valid_types=[x for x in valid_types if x not in ('cambio_aceite','refrigeracion')]
        weights=[3 if t in ('cambio_aceite','cambio_filtros') else 1 for t in valid_types]
        if day.month in (6,7,8):weights=[w*4 if t=='aire_acondicionado' else w for t,w in zip(valid_types,weights)]
        if day.month in (11,12,1,2):weights=[w*2 if t=='cambio_bateria' else w for t,w in zip(valid_types,weights)]
        repair=rng.choices(valid_types,weights)[0]
        entry=day.replace(hour=rng.randint(8,15),minute=0,second=0,microsecond=0)
        exit_=entry+timedelta(hours=rng.randint(2,24))
        for code,pname,qty in REPAIRS[repair]:
            rid=f'R{i:06d}';need[code]+=qty
            repairs.append(dict(id_orden=f'O{i:06d}',id_vehiculo=vkey,marca=brand,modelo=model,cilindrada=cc or '',combustible=fuel,año_fabricacion=year,fecha_entrada=entry.strftime(DATE_FMT),fecha_salida=exit_.strftime(DATE_FMT),id_reparacion=rid,reparaciones=repair,fecha_reparacion=entry.strftime(DATE_FMT),repuesto_necesario=pname,codigo_repuesto=code,cantidad_utilizada=qty))
    # Compras simuladas con fecha anterior a los consumos, para demostrar consultas de inventario.
    stocks=[]
    for idx,(code,amount) in enumerate(sorted(need.items()),1):
        name=next(nm for options in REPAIRS.values() for cd,nm,_ in options if cd==code)
        stocks.append(dict(id_movimiento=f'C{idx:04d}',reparacion='varias',repuesto=name,codigo_repuesto=code,cantidad=amount+30,fecha_adquisicion='01/01/2023',coste_unitario=round(rng.uniform(4,110),2),plazo_entrega_dias=rng.randint(1,7)))
    for filename,cols,rows in [('reparaciones.csv',FIELDS_REP,repairs),('adquisiciones.csv',FIELDS_STOCK,stocks)]:
        with (output/filename).open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader();writer.writerows(rows)
    print(f'Generados: {len(repairs)} líneas de consumos, {n} órdenes, {len(stocks)} referencias en {output}')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='datos');p.add_argument('--seed',type=int,default=42);p.add_argument('--ordenes',type=int,default=1100)
    a=p.parse_args();generate(a.output,a.seed,a.ordenes)
