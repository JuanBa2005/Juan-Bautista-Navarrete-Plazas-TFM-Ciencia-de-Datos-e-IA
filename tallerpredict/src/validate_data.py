"""Validación sin PostgreSQL de los archivos simulados."""
import csv,sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from decimal import Decimal
sys.path.insert(0,str(Path(__file__).resolve().parent))
from import_csv import REQ_REP,REQ_STOCK,read_csv,positive

def validate(root):
    root=Path(root); reparaciones=list(read_csv(root/'reparaciones.csv',REQ_REP));stocks=list(read_csv(root/'adquisiciones.csv',REQ_STOCK))
    consumed=defaultdict(Decimal);bought=defaultdict(Decimal);seen=set();ids=set()
    for line,r in reparaciones:
        key=(r['id_reparacion'],r['codigo_repuesto']);assert key not in seen,(line,key);seen.add(key)
        a=datetime.strptime(r['fecha_entrada'],'%d/%m/%Y %H:%M');b=datetime.strptime(r['fecha_salida'],'%d/%m/%Y %H:%M')
        assert a<=b and 1950<=int(r['año_fabricacion'])<=2100
        consumed[r['codigo_repuesto']]+=positive(r['cantidad_utilizada']);ids.add(r['id_orden'])
    for line,r in stocks:
        assert r['id_movimiento'] not in {''}
        datetime.strptime(r['fecha_adquisicion'],'%d/%m/%Y')
        bought[r['codigo_repuesto']]+=positive(r['cantidad'])
    assert set(consumed)<=set(bought)
    assert all(bought[k]>=v for k,v in consumed.items())
    print(f'OK: {len(ids)} órdenes, {len(reparaciones)} consumos, {len(stocks)} adquisiciones, {len(consumed)} piezas; stock final no negativo.')
if __name__=='__main__':validate(sys.argv[1] if len(sys.argv)>1 else 'datos')
