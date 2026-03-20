import pytest_asyncio


@pytest_asyncio.fixture
async def service(client):
    sys_r = await client.post("/api/v1/systems/", json={"name": "Sys"})
    svc_r = await client.post(f"/api/v1/systems/{sys_r.json()['id']}/services/", json={"name": "svc"})
    return svc_r.json()


async def test_create_interface_http(client, service):
    r = await client.post(f"/api/v1/services/{service['id']}/interfaces/", json={
        "name": "REST API", "type": "http", "version": "1.0",
        "spec_ref": "https://example.com/openapi.yaml",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "REST API"
    assert data["type"] == "http"
    assert data["version"] == "1.0"
    assert data["spec_ref"] == "https://example.com/openapi.yaml"
    assert data["service_id"] == service["id"]


async def test_create_interface_grpc(client, service):
    r = await client.post(f"/api/v1/services/{service['id']}/interfaces/", json={
        "name": "gRPC API", "type": "grpc",
    })
    assert r.status_code == 201
    assert r.json()["type"] == "grpc"


async def test_list_interfaces(client, service):
    await client.post(f"/api/v1/services/{service['id']}/interfaces/", json={"name": "API v1", "type": "http"})
    await client.post(f"/api/v1/services/{service['id']}/interfaces/", json={"name": "gRPC", "type": "grpc"})
    r = await client.get(f"/api/v1/services/{service['id']}/interfaces/")
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_list_interfaces_empty(client, service):
    r = await client.get(f"/api/v1/services/{service['id']}/interfaces/")
    assert r.status_code == 200
    assert r.json() == []


async def test_update_interface(client, service):
    cr = await client.post(f"/api/v1/services/{service['id']}/interfaces/", json={"name": "Old", "type": "http"})
    iface_id = cr.json()["id"]
    r = await client.patch(f"/api/v1/services/{service['id']}/interfaces/{iface_id}", json={
        "name": "Updated", "version": "2.0",
    })
    assert r.status_code == 200
    assert r.json()["name"] == "Updated"
    assert r.json()["version"] == "2.0"
    assert r.json()["type"] == "http"  # unchanged


async def test_delete_interface(client, service):
    cr = await client.post(f"/api/v1/services/{service['id']}/interfaces/", json={"name": "API", "type": "http"})
    iface_id = cr.json()["id"]
    r = await client.delete(f"/api/v1/services/{service['id']}/interfaces/{iface_id}")
    assert r.status_code == 204


async def test_get_interface_direct(client, service):
    cr = await client.post(f"/api/v1/services/{service['id']}/interfaces/", json={"name": "Direct API", "type": "http"})
    iface_id = cr.json()["id"]
    r = await client.get(f"/api/v1/interfaces/{iface_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "Direct API"
    assert r.json()["service_id"] == service["id"]


async def test_get_interface_direct_not_found(client):
    r = await client.get("/api/v1/interfaces/nonexistent")
    assert r.status_code == 404
