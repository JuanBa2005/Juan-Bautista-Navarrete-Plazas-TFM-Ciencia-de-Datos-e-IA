from fastapi.testclient import TestClient
from src import app as module

def test_home_without_postgres(monkeypatch):
    monkeypatch.setattr(module, 'fetch', lambda *a,**k: (_ for _ in ()).throw(RuntimeError('offline')))
    response=TestClient(module.app).get('/')
    assert response.status_code==503
    assert 'No hay conexión' in response.text

def test_pages_render_with_sample(monkeypatch):
    monkeypatch.setattr(module, 'fetch', lambda *a,**k: [])
    client=TestClient(module.app)
    for path in ['/vehiculos','/ordenes','/inventario','/recomendaciones','/importar']:
        resp=client.get(path)
        assert resp.status_code==200, path
        assert 'TallerPredict' in resp.text
