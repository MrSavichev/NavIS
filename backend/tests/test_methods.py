import pytest_asyncio


@pytest_asyncio.fixture
async def interface(client):
    sys_r = await client.post("/api/v1/systems/", json={"name": "Sys"})
    svc_r = await client.post(f"/api/v1/systems/{sys_r.json()['id']}/services/", json={"name": "svc"})
    iface_r = await client.post(
        f"/api/v1/services/{svc_r.json()['id']}/interfaces/",
        json={"name": "API", "type": "http"},
    )
    return iface_r.json()


async def test_create_method(client, interface):
    r = await client.post(f"/api/v1/interfaces/{interface['id']}/methods/", json={
        "name": "getUser", "http_method": "GET",
        "path": "/api/v1/users/{id}", "description": "Get user by ID",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "getUser"
    assert data["http_method"] == "GET"
    assert data["path"] == "/api/v1/users/{id}"
    assert data["description"] == "Get user by ID"
    assert data["interface_id"] == interface["id"]


async def test_create_method_with_schema(client, interface):
    r = await client.post(f"/api/v1/interfaces/{interface['id']}/methods/", json={
        "name": "createUser", "http_method": "POST", "path": "/users",
        "request_schema": {"type": "object", "properties": {"name": {"type": "string"}}},
        "response_schema": {"type": "object", "properties": {"id": {"type": "string"}}},
    })
    assert r.status_code == 201
    data = r.json()
    assert data["request_schema"]["type"] == "object"
    assert data["response_schema"]["type"] == "object"


async def test_create_method_unknown_interface(client):
    r = await client.post("/api/v1/interfaces/bad-id/methods/", json={"name": "m", "http_method": "GET"})
    assert r.status_code == 404


async def test_list_methods(client, interface):
    await client.post(f"/api/v1/interfaces/{interface['id']}/methods/", json={"name": "listUsers", "http_method": "GET", "path": "/users"})
    await client.post(f"/api/v1/interfaces/{interface['id']}/methods/", json={"name": "createUser", "http_method": "POST", "path": "/users"})
    r = await client.get(f"/api/v1/interfaces/{interface['id']}/methods/")
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_get_method(client, interface):
    cr = await client.post(f"/api/v1/interfaces/{interface['id']}/methods/", json={
        "name": "deleteUser", "http_method": "DELETE", "path": "/users/{id}",
    })
    method_id = cr.json()["id"]
    r = await client.get(f"/api/v1/interfaces/{interface['id']}/methods/{method_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "deleteUser"


async def test_get_method_not_found(client, interface):
    r = await client.get(f"/api/v1/interfaces/{interface['id']}/methods/nonexistent")
    assert r.status_code == 404


async def test_update_method(client, interface):
    cr = await client.post(f"/api/v1/interfaces/{interface['id']}/methods/", json={
        "name": "oldName", "http_method": "GET", "path": "/old",
    })
    method_id = cr.json()["id"]
    r = await client.patch(f"/api/v1/interfaces/{interface['id']}/methods/{method_id}", json={
        "name": "newName", "path": "/new", "description": "Updated",
    })
    assert r.status_code == 200
    assert r.json()["name"] == "newName"
    assert r.json()["path"] == "/new"
    assert r.json()["description"] == "Updated"
    assert r.json()["http_method"] == "GET"  # unchanged


async def test_delete_method(client, interface):
    cr = await client.post(f"/api/v1/interfaces/{interface['id']}/methods/", json={
        "name": "toDelete", "http_method": "DELETE", "path": "/x",
    })
    method_id = cr.json()["id"]
    r = await client.delete(f"/api/v1/interfaces/{interface['id']}/methods/{method_id}")
    assert r.status_code == 204
    r2 = await client.get(f"/api/v1/interfaces/{interface['id']}/methods/{method_id}")
    assert r2.status_code == 404


async def test_method_sources_empty(client, interface):
    cr = await client.post(f"/api/v1/interfaces/{interface['id']}/methods/", json={
        "name": "m", "http_method": "GET", "path": "/m",
    })
    method_id = cr.json()["id"]
    r = await client.get(f"/api/v1/methods/{method_id}/sources")
    assert r.status_code == 200
    assert r.json() == []
