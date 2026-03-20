import pytest_asyncio


@pytest_asyncio.fixture
async def system(client):
    r = await client.post("/api/v1/systems/", json={"name": "Test System"})
    return r.json()


async def test_create_service(client, system):
    r = await client.post(f"/api/v1/systems/{system['id']}/services/", json={
        "name": "payment-service", "description": "Handles payments",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "payment-service"
    assert data["description"] == "Handles payments"
    assert data["system_id"] == system["id"]


async def test_create_service_unknown_system(client):
    r = await client.post("/api/v1/systems/bad-id/services/", json={"name": "svc"})
    assert r.status_code == 404


async def test_list_services(client, system):
    await client.post(f"/api/v1/systems/{system['id']}/services/", json={"name": "svc-1"})
    await client.post(f"/api/v1/systems/{system['id']}/services/", json={"name": "svc-2"})
    r = await client.get(f"/api/v1/systems/{system['id']}/services/")
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_list_services_empty(client, system):
    r = await client.get(f"/api/v1/systems/{system['id']}/services/")
    assert r.status_code == 200
    assert r.json() == []


async def test_get_service(client, system):
    cr = await client.post(f"/api/v1/systems/{system['id']}/services/", json={"name": "my-svc"})
    svc_id = cr.json()["id"]
    r = await client.get(f"/api/v1/systems/{system['id']}/services/{svc_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "my-svc"


async def test_update_service(client, system):
    cr = await client.post(f"/api/v1/systems/{system['id']}/services/", json={"name": "old"})
    svc_id = cr.json()["id"]
    r = await client.patch(f"/api/v1/systems/{system['id']}/services/{svc_id}", json={
        "name": "new", "description": "Updated desc",
    })
    assert r.status_code == 200
    assert r.json()["name"] == "new"
    assert r.json()["description"] == "Updated desc"


async def test_delete_service(client, system):
    cr = await client.post(f"/api/v1/systems/{system['id']}/services/", json={"name": "to-delete"})
    svc_id = cr.json()["id"]
    r = await client.delete(f"/api/v1/systems/{system['id']}/services/{svc_id}")
    assert r.status_code == 204


async def test_delete_service_not_found(client, system):
    r = await client.delete(f"/api/v1/systems/{system['id']}/services/nonexistent")
    assert r.status_code == 404


async def test_get_service_direct(client, system):
    cr = await client.post(f"/api/v1/systems/{system['id']}/services/", json={"name": "direct-svc"})
    svc_id = cr.json()["id"]
    r = await client.get(f"/api/v1/services/{svc_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "direct-svc"
    assert r.json()["system_id"] == system["id"]
