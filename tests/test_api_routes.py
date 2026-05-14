def test_projects_crud_and_filters(client, oid_headers):
    create_payload = {
        "name": "Project One",
        "techStack": ["fastapi", "sqlite"],
        "urls": ["https://example.com/project-1"],
        "description": "desc",
        "tags": ["backend", "api"],
    }

    res = client.post("/api/projects", json=create_payload, headers=oid_headers("user-1"))
    assert res.status_code == 201
    project = res.json()
    project_id = project["id"]

    res = client.get("/api/projects", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == project_id for item in res.json()["items"])

    res = client.get(f"/api/projects/{project_id}", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert res.json()["name"] == "Project One"

    res = client.get("/api/projects/by-tag/backend", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == project_id for item in res.json()["items"])

    res = client.get("/api/projects/by-tech/fastapi", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == project_id for item in res.json()["items"])

    res = client.get("/api/projects?tags=backend,api&techs=fastapi,sqlite", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == project_id for item in res.json()["items"])

    patch_res = client.patch(
        f"/api/projects/{project_id}",
        json={"description": "updated", "tags": ["backend", "updated"]},
        headers=oid_headers("user-1"),
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["description"] == "updated"
    assert patch_res.json()["tags"] == ["backend", "updated"]

    res = client.delete(f"/api/projects/{project_id}", headers=oid_headers("user-1"))
    assert res.status_code == 204

    res = client.get(f"/api/projects/{project_id}", headers=oid_headers("user-1"))
    assert res.status_code == 404


def test_projects_are_isolated_by_oid(client, oid_headers):
    payload = {
        "name": "Private Project",
        "techStack": ["python"],
        "urls": [],
        "description": "desc",
        "tags": ["private"],
    }
    create_res = client.post("/api/projects", json=payload, headers=oid_headers("user-a"))
    assert create_res.status_code == 201
    project_id = create_res.json()["id"]

    forbidden_read = client.get(f"/api/projects/{project_id}", headers=oid_headers("user-b"))
    assert forbidden_read.status_code == 404

    forbidden_delete = client.delete(f"/api/projects/{project_id}", headers=oid_headers("user-b"))
    assert forbidden_delete.status_code == 404


def test_experiences_crud_and_filters(client, oid_headers):
    payload = {
        "companyName": "Acme",
        "startDate": "10-01-2024",
        "endDate": None,
        "position": "Backend Engineer",
        "description": "Built APIs",
        "location": "Bengaluru",
    }
    create_res = client.post("/api/experiences", json=payload, headers=oid_headers("user-1"))
    assert create_res.status_code == 201
    experience_id = create_res.json()["id"]

    res = client.get("/api/experiences", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == experience_id for item in res.json()["items"])

    res = client.get(f"/api/experiences/{experience_id}", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert res.json()["companyName"] == "Acme"

    res = client.get("/api/experiences?position=Backend%20Engineer", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == experience_id for item in res.json()["items"])

    res = client.get("/api/experiences/by-position/Backend%20Engineer", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == experience_id for item in res.json()["items"])

    res = client.get("/api/experiences/by-company/Acme", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == experience_id for item in res.json()["items"])

    patch_res = client.patch(
        f"/api/experiences/{experience_id}",
        json={"endDate": "31-12-2024", "description": "Updated"},
        headers=oid_headers("user-1"),
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["endDate"] == "31-12-2024"

    delete_res = client.delete(f"/api/experiences/{experience_id}", headers=oid_headers("user-1"))
    assert delete_res.status_code == 204

    missing_res = client.get(f"/api/experiences/{experience_id}", headers=oid_headers("user-1"))
    assert missing_res.status_code == 404


def test_experience_date_accepts_freeform_string(client, oid_headers):
    payload = {
        "companyName": "Acme",
        "startDate": "Jan 2024 to Present",
        "endDate": None,
        "position": "Engineer",
        "description": "desc",
        "location": "BLR",
    }
    res = client.post("/api/experiences", json=payload, headers=oid_headers("user-1"))
    assert res.status_code == 201
    assert res.json()["startDate"] == "Jan 2024 to Present"


def test_achievements_crud_and_filters(client, oid_headers):
    payload = {
        "name": "Hackathon Winner",
        "link": "https://example.com/cert",
        "organisation": "Acme Org",
        "date": "01-02-2025",
    }
    create_res = client.post("/api/achievements", json=payload, headers=oid_headers("user-1"))
    assert create_res.status_code == 201
    achievement_id = create_res.json()["id"]

    res = client.get("/api/achievements", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == achievement_id for item in res.json()["items"])

    res = client.get(f"/api/achievements/{achievement_id}", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert res.json()["name"] == "Hackathon Winner"

    res = client.get("/api/achievements?organisation=Acme%20Org", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == achievement_id for item in res.json()["items"])

    res = client.get("/api/achievements/by-organisation/Acme%20Org", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == achievement_id for item in res.json()["items"])

    res = client.get("/api/achievements/by-name/Hackathon%20Winner", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == achievement_id for item in res.json()["items"])

    patch_res = client.patch(
        f"/api/achievements/{achievement_id}",
        json={"name": "Hackathon Winner Updated"},
        headers=oid_headers("user-1"),
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Hackathon Winner Updated"

    delete_res = client.delete(f"/api/achievements/{achievement_id}", headers=oid_headers("user-1"))
    assert delete_res.status_code == 204

    missing_res = client.get(f"/api/achievements/{achievement_id}", headers=oid_headers("user-1"))
    assert missing_res.status_code == 404


def test_achievement_date_accepts_freeform_string(client, oid_headers):
    payload = {
        "name": "Award",
        "link": "https://example.com",
        "organisation": "Org",
        "date": "Spring 2025",
    }
    res = client.post("/api/achievements", json=payload, headers=oid_headers("user-1"))
    assert res.status_code == 201
    assert res.json()["date"] == "Spring 2025"


def test_missing_oid_claim_returns_401(client):
    res = client.get("/api/projects")
    assert res.status_code == 401
    assert "Missing oid claim" in res.json()["detail"]
