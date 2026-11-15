from datetime import date
from src.forecast import months_ago, recommend

def test_months_ago():
    assert months_ago(date(2026,1,3),6)==date(2025,7,1)
    assert months_ago(date(2026,11,8),6)==date(2026,5,1)

def test_zero_usage_no_purchase():
    x=recommend('0','5',2)
    assert x['suggested_buy']==0 and 'Sin demanda' in x['label']

def test_reorder_and_positive():
    x=recommend('180','1',3)
    assert x['forecast_30']==30
    assert x['reorder_point']==10
    assert x['suggested_buy']==39

def test_sufficient_stock():
    assert recommend('180','100',2)['suggested_buy']==0
