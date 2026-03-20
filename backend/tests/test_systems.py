async def test_create_system(client):
    r = await client.post("/api/v1/systems/", json={
        "name": "Billing System", "owner": "team-billing",
        "tags": ["billing", "payments"], "environments": ["prod", "staging"],
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Billing System"
    assert data["owner"] == "team-billing"
    assert data["tags"] == ["billing", "payments"]
    assert data["environments"] == ["prod", "staging"]
    assert "id" in data


async def test_create_system_minimal(client):
    r = await client.post("/api/v1/systems/", json={"name": "Minimal"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Minimal"
    assert data["owner"] is None
    assert data["tags"] == []


async def test_list_systems(client):
    await client.post("/api/v1/systems/", json={"name": "System A"})
    await client.post("/api/v1/systems/", json={"name": "System B"})
    r = await client.get("/api/v1/systems/")
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_get_system(client):
    cr = await client.post("/api/v1/systems/", json={"name": "My System"})
    sys_id = cr.json()["id"]
    r = await client.get(f"/api/v1/systems/{sys_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "My System"


async def test_get_system_not_found(client):
    r = await client.get("/api/v1/systems/nonexistent-id")
    assert r.status_code == 404


async def test_update_system(client):
    cr = await client.post("/api/v1/systems/", json={"name": "Old Name", "tags": ["old"]})
    sys_id = cr.json()["id"]
    r = await client.patch(f"/api/v1/systems/{sys_id}", json={"name": "New Name", "tags": ["updated"]})
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"
    assert r.json()["tags"] == ["updated"]


async def test_update_system_partial(client):
    cr = await client.post("/api/v1/systems/", json={"name": "System", "owner": "team-a"})
    sys_id = cr.json()["id"]
    r = await client.patch(f"/api/v1/systems/{sys_id}", json={"owner": "team-b"})
    assert r.status_code == 200
    assert r.json()["name"] == "System"   # unchanged
    assert r.json()["owner"] == "team-b"  # updated


async def test_delete_system(client):
    cr = await client.post("/api/v1/systems/", json={"name": "To Delete"})
    sys_id = cr.json()["id"]
    r = await client.delete(f"/api/v1/systems/{sys_id}")
    assert r.status_code == 204
    r2 = await client.get(f"/api/v1/systems/{sys_id}")
    assert r2.status_code == 404


async def test_delete_system_cascades_to_services(client):
    cr = await client.post("/api/v1/systems/", json={"name": "Parent"})
    sys_id = cr.json()["id"]
    await client.post(f"/api/v1/systems/{sys_id}/services/", json={"name": "child-svc"})

    await client.delete(f"/api/v1/systems/{sys_id}")

    # Каскадное удаление сработало — сервисов нет
    r = await client.get(f"/api/v1/systems/{sys_id}/services/")
    assert r.status_code == 200
    assert r.json() == []
