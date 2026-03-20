import pytest_asyncio


@pytest_asyncio.fixture
async def populated(client):
    """Заполняет БД: система → сервис → интерфейс → метод."""
    sys_r = await client.post("/api/v1/systems/", json={
        "name": "Billing System", "description": "Handles billing and invoices",
    })
    sys_id = sys_r.json()["id"]

    svc_r = await client.post(f"/api/v1/systems/{sys_id}/services/", json={"name": "invoice-service"})
    svc_id = svc_r.json()["id"]

    iface_r = await client.post(f"/api/v1/services/{svc_id}/interfaces/", json={
        "name": "Billing API", "type": "http",
    })
    iface_id = iface_r.json()["id"]

    method_r = await client.post(f"/api/v1/interfaces/{iface_id}/methods/", json={
        "name": "createInvoice", "http_method": "POST", "path": "/invoices",
        "description": "Creates a new invoice",
    })

    return {
        "system_id": sys_id,
        "service_id": svc_id,
        "interface_id": iface_id,
        "method_id": method_r.json()["id"],
    }


async def test_search_system_by_name(client, populated):
    r = await client.get("/api/v1/search/", params={"q": "Billing"})
    assert r.status_code == 200
    systems = [x for x in r.json() if x["type"] == "system"]
    assert len(systems) >= 1
    assert systems[0]["label"] == "Billing System"


async def test_search_system_url(client, populated):
    r = await client.get("/api/v1/search/", params={"q": "Billing System"})
    systems = [x for x in r.json() if x["type"] == "system"]
    assert systems[0]["url"] == f"/systems/{populated['system_id']}"


async def test_search_service_url(client, populated):
    r = await client.get("/api/v1/search/", params={"q": "invoice-service"})
    services = [x for x in r.json() if x["type"] == "service"]
    assert len(services) >= 1
    # Сервис ведёт на страницу системы
    assert services[0]["url"] == f"/systems/{populated['system_id']}"


async def test_search_method_by_name(client, populated):
    r = await client.get("/api/v1/search/", params={"q": "createInvoice"})
    assert r.status_code == 200
    methods = [x for x in r.json() if x["type"] == "method"]
    assert len(methods) >= 1
    assert methods[0]["label"] == "createInvoice"


async def test_search_method_url(client, populated):
    r = await client.get("/api/v1/search/", params={"q": "createInvoice"})
    methods = [x for x in r.json() if x["type"] == "method"]
    expected_url = f"/methods/{populated['interface_id']}/{populated['method_id']}"
    assert methods[0]["url"] == expected_url


async def test_search_method_by_path(client, populated):
    r = await client.get("/api/v1/search/", params={"q": "/invoices"})
    methods = [x for x in r.json() if x["type"] == "method"]
    assert len(methods) >= 1


async def test_search_by_description(client, populated):
    r = await client.get("/api/v1/search/", params={"q": "invoices"})
    assert r.status_code == 200
    assert len(r.json()) >= 1


async def test_search_no_results(client, populated):
    r = await client.get("/api/v1/search/", params={"q": "xyznonexistent999"})
    assert r.status_code == 200
    assert r.json() == []


async def test_search_too_short(client):
    r = await client.get("/api/v1/search/", params={"q": "x"})
    assert r.status_code == 422  # min_length=2 нарушен
