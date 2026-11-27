"""Pruebas de aceptación del servicio con la muestra histórica del TFM."""
from pathlib import Path
import sys
import math

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from servicios.datos import cargar_gold, reconstruir_historico
from servicios.predicciones import predecir_global, predecir_individual, obtener_historico


def main():
    gold = cargar_gold()
    historico = reconstruir_historico(gold)
    previsiones = predecir_global(historico)
    individual = predecir_individual(historico, 'REP-0001')
    assert len(gold) == 2640
    assert len(historico) == 2880
    assert len(previsiones) == 80
    assert str(previsiones.mes_referencia.iloc[0].date()) == '2023-12-01'
    assert str(previsiones.mes_prediccion.iloc[0].date()) == '2024-01-01'
    assert (previsiones.prediccion > 0).sum() == 41
    assert (previsiones.prediccion == 0).sum() == 39
    assert math.isclose(individual.prediccion, 13/3)
    for fila in previsiones.itertuples():
        serie = obtener_historico(historico, fila.part_code)
        assert len(serie) == 36
        assert math.isclose(fila.prediccion, serie.consumo.tail(3).mean())
    try:
        predecir_individual(historico, 'NO-EXISTE')
    except ValueError:
        pass
    else:
        raise AssertionError('No se detectó el repuesto inexistente.')
    print(f'Gold: {len(gold)} filas')
    print(f'Histórico: {len(historico)} filas')
    print(f'Repuestos: {len(previsiones)}')
    print(f'Referencia: {previsiones.mes_referencia.iloc[0]:%Y-%m}')
    print(f'Previsión: {previsiones.mes_prediccion.iloc[0]:%Y-%m}')
    print(f'Previsiones positivas: {(previsiones.prediccion > 0).sum()}')
    print(f'Previsiones cero: {(previsiones.prediccion == 0).sum()}')
    print(f'REP-0001: {individual.prediccion:.4f} {individual.unit}')
    print('Todas las comprobaciones superadas.')


if __name__ == '__main__':
    main()
