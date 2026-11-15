"""Heurística de inventario como línea base, NO modelo ML validado."""
from datetime import date
from decimal import Decimal, ROUND_CEILING

def months_ago(today:date, count:int):
    n=today.year*12+today.month-1-count
    return date(n//12,(n%12)+1,1)

def recommend(used_6months,stock,lead_days):
    """Media mensual 6 meses / 30 días, safety 7 días, horizonte 30 días.
    Puntos de pedido y recomendación orientativos; no contemplan pedidos en tránsito.
    """
    usage=max(Decimal('0'),Decimal(str(used_6months)))
    stock=Decimal(str(stock))
    lead=max(0,int(lead_days))
    daily=usage/Decimal(180)
    forecast=daily*30
    reorder_point=daily*(lead+7)
    target=daily*(30+lead+7)
    buy=max(Decimal(0),target-stock).to_integral_value(rounding=ROUND_CEILING)
    if usage==0:
        label='Sin demanda reciente · revisar bajo pedido'
    elif stock<=reorder_point:
        label='Reponer'
    else:
        label='Stock suficiente'
    return {'forecast_30':float(forecast.quantize(Decimal('0.01'))),
            'reorder_point':float(reorder_point.quantize(Decimal('0.01'))),
            'suggested_buy':int(buy) if stock<=reorder_point and usage>0 else 0,
            'label':label}
