"""Pruebas de la capa de presentación con la muestra actual del TFM."""
from pathlib import Path
import sys
import io
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from servicios.datos import cargar_gold, reconstruir_historico
from servicios.predicciones import predecir_global
from servicios.vista_global import filtrar_previsiones, preparar_tabla, exportar_csv, ranking

p = predecir_global(reconstruir_historico(cargar_gold()))
assert len(p) == 80
assert len(filtrar_previsiones(p, estado='Positivo')) == 41
assert len(filtrar_previsiones(p, estado='Cero')) == 39
assert len(filtrar_previsiones(p, 'rep-0001')) == 1
assert filtrar_previsiones(p, '[sin coincidencias]').empty
assert '10/2023' in preparar_tabla(p).columns
for u in p.unit.unique():
    f = filtrar_previsiones(p, unidad=u, orden='Mayor previsión')
    assert f.unit.eq(u).all() and f.prediccion.is_monotonic_decreasing
    r = ranking(p, u)
    assert len(r) <= 10 and r.unit.eq(u).all() and r.prediccion.gt(0).all()
    assert r.prediccion.is_monotonic_decreasing
csv = exportar_csv(p)
recuperado = pd.read_csv(io.BytesIO(csv), sep=';', decimal=',', encoding='utf-8-sig')
assert len(recuperado) == 80
assert (recuperado.prediccion - p.prediccion).abs().max() < 1e-10
print('80 repuestos; 41 previsiones positivas; 39 cero.')
print('Filtros, ordenación, tabla, ranking y CSV: comprobaciones superadas.')
