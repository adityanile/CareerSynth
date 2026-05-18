import io
import zipfile


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


def test_educations_crud_and_filters(client, oid_headers):
    payload = {
        "degreeName": "B.Tech Computer Science",
        "location": "Bengaluru",
        "startYear": "2020",
        "endYear": "2024",
        "cgpaOrPercentage": "8.6 CGPA",
    }
    create_res = client.post("/api/educations", json=payload, headers=oid_headers("user-1"))
    assert create_res.status_code == 201
    education_id = create_res.json()["id"]

    res = client.get("/api/educations", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == education_id for item in res.json()["items"])

    res = client.get(f"/api/educations/{education_id}", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert res.json()["degreeName"] == "B.Tech Computer Science"

    res = client.get(
        "/api/educations?degree_name=B.Tech%20Computer%20Science",
        headers=oid_headers("user-1"),
    )
    assert res.status_code == 200
    assert any(item["id"] == education_id for item in res.json()["items"])

    res = client.get("/api/educations/by-degree/B.Tech%20Computer%20Science", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == education_id for item in res.json()["items"])

    patch_res = client.patch(
        f"/api/educations/{education_id}",
        json={"endYear": None, "cgpaOrPercentage": "87%"},
        headers=oid_headers("user-1"),
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["endYear"] is None
    assert patch_res.json()["cgpaOrPercentage"] == "87%"

    delete_res = client.delete(f"/api/educations/{education_id}", headers=oid_headers("user-1"))
    assert delete_res.status_code == 204

    missing_res = client.get(f"/api/educations/{education_id}", headers=oid_headers("user-1"))
    assert missing_res.status_code == 404


def test_resumes_crud_and_filters(client, oid_headers):
    payload = {
        "resumeName": "Backend Resume",
        "resumeDescription": "ATS optimized for backend roles",
        "resume": "\\documentclass{article}\\begin{document}Backend\\end{document}",
    }
    create_res = client.post("/api/resumes", json=payload, headers=oid_headers("user-1"))
    assert create_res.status_code == 201
    resume_id = create_res.json()["id"]

    res = client.get("/api/resumes", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == resume_id for item in res.json()["items"])

    res = client.get("/api/resumes?resume_name=Backend%20Resume", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert any(item["id"] == resume_id for item in res.json()["items"])

    res = client.get(f"/api/resumes/{resume_id}", headers=oid_headers("user-1"))
    assert res.status_code == 200
    assert res.json()["resumeName"] == "Backend Resume"
    assert "userReference" not in res.json()

    patch_res = client.patch(
        f"/api/resumes/{resume_id}",
        json={"resumeDescription": "Updated description"},
        headers=oid_headers("user-1"),
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["resumeDescription"] == "Updated description"

    delete_res = client.delete(f"/api/resumes/{resume_id}", headers=oid_headers("user-1"))
    assert delete_res.status_code == 204

    missing_res = client.get(f"/api/resumes/{resume_id}", headers=oid_headers("user-1"))
    assert missing_res.status_code == 404


def test_resumes_are_isolated_by_oid(client, oid_headers):
    payload = {
        "resumeName": "Private Resume",
        "resumeDescription": "Private",
        "resume": "\\documentclass{article}\\begin{document}Private\\end{document}",
    }
    create_res = client.post("/api/resumes", json=payload, headers=oid_headers("user-a"))
    assert create_res.status_code == 201
    resume_id = create_res.json()["id"]

    forbidden_read = client.get(f"/api/resumes/{resume_id}", headers=oid_headers("user-b"))
    assert forbidden_read.status_code == 404

    forbidden_delete = client.delete(f"/api/resumes/{resume_id}", headers=oid_headers("user-b"))
    assert forbidden_delete.status_code == 404


def test_resume_delete_calls_blob_cleanup(client, oid_headers, monkeypatch):
    from api.routes import resumes as resumes_route

    called: dict[str, str] = {}

    def _fake_delete_resume_blob_if_needed(blob_url: str) -> None:
        called["blob_url"] = blob_url

    monkeypatch.setattr(resumes_route, "_delete_resume_blob_if_needed", _fake_delete_resume_blob_if_needed)

    payload = {
        "resumeName": "Blob Resume",
        "resumeDescription": "Stored in blob",
        "resume": "https://example.blob.core.windows.net/container/file.pdf",
    }
    create_res = client.post("/api/resumes", json=payload, headers=oid_headers("user-1"))
    assert create_res.status_code == 201
    resume_id = create_res.json()["id"]

    delete_res = client.delete(f"/api/resumes/{resume_id}", headers=oid_headers("user-1"))
    assert delete_res.status_code == 204
    assert called["blob_url"] == "https://example.blob.core.windows.net/container/file.pdf"


def test_resume_delete_returns_502_if_blob_cleanup_fails(client, oid_headers, monkeypatch):
    from api.routes import resumes as resumes_route

    def _failing_delete_resume_blob_if_needed(blob_url: str) -> None:
        raise RuntimeError("blob delete failed")

    monkeypatch.setattr(resumes_route, "_delete_resume_blob_if_needed", _failing_delete_resume_blob_if_needed)

    payload = {
        "resumeName": "Blob Resume",
        "resumeDescription": "Stored in blob",
        "resume": "https://example.blob.core.windows.net/container/file.pdf",
    }
    create_res = client.post("/api/resumes", json=payload, headers=oid_headers("user-1"))
    assert create_res.status_code == 201
    resume_id = create_res.json()["id"]

    delete_res = client.delete(f"/api/resumes/{resume_id}", headers=oid_headers("user-1"))
    assert delete_res.status_code == 502
    assert "Failed to delete resume blob" in delete_res.json()["detail"]

    # Record should remain when blob cleanup fails.
    get_res = client.get(f"/api/resumes/{resume_id}", headers=oid_headers("user-1"))
    assert get_res.status_code == 200


def test_parse_resume_upload_pdf_returns_structured_output(client, oid_headers, monkeypatch):
    from api.routes import resumes as resumes_route

    async def _fake_parse_resume_from_pdf(file_name: str, file_bytes: bytes):
        assert file_name == "resume.pdf"
        assert file_bytes.startswith(b"%PDF")
        return resumes_route.ParsedResumeOutput(
            projects=[
                {
                    "projectName": "CareerSynth",
                    "description": "Built resume platform",
                    "techStack": ["FastAPI", "React"],
                }
            ],
            experiences=[],
            achievements=[],
            educations=[],
        )

    monkeypatch.setattr(resumes_route, "_parse_resume_from_pdf", _fake_parse_resume_from_pdf)

    res = client.post(
        "/api/resumes/parse",
        files={"file": ("resume.pdf", b"%PDF-1.7 fake", "application/pdf")},
        headers=oid_headers("user-1"),
    )

    assert res.status_code == 200
    body = res.json()
    assert body["projects"][0]["projectName"] == "CareerSynth"
    assert body["experiences"] == []


def test_parse_resume_upload_docx_uses_text_parser(client, oid_headers, monkeypatch):
    from api.routes import resumes as resumes_route

    called: dict[str, str] = {}

    def _fake_extract_docx_text(file_bytes: bytes) -> str:
        called["extract_called"] = "1"
        assert file_bytes
        return "John Doe\nBackend Engineer"

    async def _fake_parse_resume_from_text(resume_text: str):
        called["text"] = resume_text
        return resumes_route.ParsedResumeOutput(
            projects=[],
            experiences=[],
            achievements=[
                {
                    "name": "Winner",
                    "organisation": "HackFest",
                    "date": "2025",
                    "link": "https://example.com",
                }
            ],
            educations=[],
        )

    monkeypatch.setattr(resumes_route, "_extract_docx_text", _fake_extract_docx_text)
    monkeypatch.setattr(resumes_route, "_parse_resume_from_text", _fake_parse_resume_from_text)

    fake_docx = io.BytesIO()
    with zipfile.ZipFile(fake_docx, "w") as archive:
        archive.writestr("word/document.xml", "<w:document></w:document>")

    res = client.post(
        "/api/resumes/parse",
        files={
            "file": (
                "resume.docx",
                fake_docx.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        headers=oid_headers("user-1"),
    )

    assert res.status_code == 200
    body = res.json()
    assert called["extract_called"] == "1"
    assert called["text"] == "John Doe\nBackend Engineer"
    assert body["achievements"][0]["organisation"] == "HackFest"


def test_parse_resume_text_endpoint_returns_structured_output(client, oid_headers, monkeypatch):
    from api.routes import resumes as resumes_route

    async def _fake_parse_resume_from_text(resume_text: str):
        assert "Backend Engineer" in resume_text
        return resumes_route.ParsedResumeOutput(
            projects=[],
            experiences=[
                {
                    "companyName": "Acme",
                    "position": "Backend Engineer",
                    "description": "Built APIs",
                    "startDate": "2023",
                    "endDate": None,
                    "location": "Bengaluru",
                }
            ],
            achievements=[],
            educations=[],
        )

    monkeypatch.setattr(resumes_route, "_parse_resume_from_text", _fake_parse_resume_from_text)

    res = client.post(
        "/api/resumes/parse",
        json={"text": "Worked as Backend Engineer at Acme"},
        headers=oid_headers("user-1"),
    )

    assert res.status_code == 200
    body = res.json()
    assert body["experiences"][0]["companyName"] == "Acme"
    assert body["experiences"][0]["endDate"] is None


def test_parse_resume_upload_rejects_unsupported_file(client, oid_headers):
    res = client.post(
        "/api/resumes/parse",
        files={"file": ("resume.txt", b"plain text", "text/plain")},
        headers=oid_headers("user-1"),
    )

    assert res.status_code == 400
    assert "Only PDF and DOCX files are supported." in res.json()["detail"]


def test_parse_resume_upload_allows_octet_stream_content_type(client, oid_headers, monkeypatch):
    from api.routes import resumes as resumes_route

    async def _fake_parse_resume_from_pdf(file_name: str, file_bytes: bytes):
        assert file_name == "resume.pdf"
        assert file_bytes.startswith(b"%PDF")
        return resumes_route.ParsedResumeOutput(
            projects=[],
            experiences=[],
            achievements=[],
            educations=[],
        )

    monkeypatch.setattr(resumes_route, "_parse_resume_from_pdf", _fake_parse_resume_from_pdf)

    res = client.post(
        "/api/resumes/parse",
        files={"file": ("resume.pdf", b"%PDF-1.7 fake", "application/octet-stream")},
        headers=oid_headers("user-1"),
    )

    assert res.status_code == 200


def test_save_parsed_resume_to_system_persists_records(client, oid_headers):
    payload = {
        "projects": [
            {
                "projectName": "CareerSynth",
                "description": "Built resume workflows",
                "techStack": ["FastAPI", "React"],
            }
        ],
        "experiences": [
            {
                "companyName": "Acme",
                "position": "Backend Engineer",
                "description": "Built APIs",
                "startDate": "2023",
                "endDate": None,
                "location": "Bengaluru",
            }
        ],
        "achievements": [
            {
                "name": "Hackathon Winner",
                "organisation": "Acme Org",
                "date": "2025",
                "link": "https://example.com/cert",
            }
        ],
        "educations": [
            {
                "degreeName": "B.Tech CSE",
                "location": "Bengaluru",
                "startYear": "2020",
                "endYear": "2024",
                "cgpaOrPercentage": "8.7",
            }
        ],
    }

    save_res = client.post(
        "/api/resumes/parse/save",
        json=payload,
        headers=oid_headers("user-1"),
    )
    assert save_res.status_code == 200
    body = save_res.json()
    assert body["saved"] == {
        "projects": 1,
        "experiences": 1,
        "achievements": 1,
        "educations": 1,
    }
    assert body["skipped"] == {
        "projects": 0,
        "experiences": 0,
        "achievements": 0,
        "educations": 0,
    }

    assert client.get("/api/projects", headers=oid_headers("user-1")).json()["items"][0]["name"] == "CareerSynth"
    assert (
        client.get("/api/experiences", headers=oid_headers("user-1")).json()["items"][0]["companyName"]
        == "Acme"
    )
    assert (
        client.get("/api/achievements", headers=oid_headers("user-1")).json()["items"][0]["name"]
        == "Hackathon Winner"
    )
    assert (
        client.get("/api/educations", headers=oid_headers("user-1")).json()["items"][0]["degreeName"]
        == "B.Tech CSE"
    )


def test_missing_oid_claim_returns_401(client):
    res = client.get("/api/projects")
    assert res.status_code == 401
    assert "Missing oid claim" in res.json()["detail"]
