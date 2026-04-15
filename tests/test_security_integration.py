from pathlib import Path

import src.api as api_module


def register_and_login(client, email="user@example.com", password="StrongPass123"):
    register = client.post("/register", json={"email": email, "password": password})
    assert register.status_code == 200

    login = client.post("/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return login.json()["token"]



def test_register_hashes_password_and_profile_hides_sensitive_fields(client):
    client.post("/register", json={"email": "hash@example.com", "password": "StrongPass123"})

    stored_user = api_module.storage.get_user_by_email("hash@example.com")
    assert stored_user is not None
    assert stored_user["password"] != "StrongPass123"

    login = client.post("/login", json={"email": "hash@example.com", "password": "StrongPass123"})
    token = login.json()["token"]
    profile = client.get("/profile", headers={"Authorization": f"Bearer {token}"})

    assert profile.status_code == 200
    assert "password" not in profile.json()
    assert "token" not in profile.json()



def test_reset_password_requires_auth_and_current_password(client):
    token = register_and_login(client)

    missing_auth = client.post("/reset-password", json={
        "current_password": "StrongPass123",
        "new_password": "NewStrongPass456",
    })
    assert missing_auth.status_code == 401

    wrong_current = client.post(
        "/reset-password",
        json={"current_password": "wrongpass", "new_password": "NewStrongPass456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert wrong_current.status_code == 401

    reset = client.post(
        "/reset-password",
        json={"current_password": "StrongPass123", "new_password": "NewStrongPass456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reset.status_code == 200

    old_login = client.post("/login", json={"email": "user@example.com", "password": "StrongPass123"})
    new_login = client.post("/login", json={"email": "user@example.com", "password": "NewStrongPass456"})

    assert old_login.status_code == 401
    assert new_login.status_code == 200



def test_upload_rejects_non_pdf_and_stores_file_inside_upload_directory(client):
    token = register_and_login(client, email="upload@example.com")

    invalid = client.post(
        "/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("../../secret.txt", b"not-a-pdf", "text/plain")},
    )
    assert invalid.status_code == 400

    valid = client.post(
        "/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("../../resume.pdf", b"%PDF-1.4 test pdf", "application/pdf")},
    )
    assert valid.status_code == 200

    stored_user = api_module.storage.get_user_by_email("upload@example.com")
    stored_path = Path(stored_user["resume_path"]).resolve()
    upload_dir = Path(api_module.UPLOAD_DIR).resolve()

    assert upload_dir in stored_path.parents
    assert stored_path.name.endswith("_resume.pdf")



def test_jobs_pagination_and_favorites_flow(client):
    token = register_and_login(client, email="jobs@example.com")

    upload = client.post(
        "/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("resume.pdf", b"%PDF-1.4 test pdf", "application/pdf")},
    )
    assert upload.status_code == 200

    invalid_page = client.get("/jobs?page=0&limit=9", headers={"Authorization": f"Bearer {token}"})
    assert invalid_page.status_code == 400

    jobs = client.get("/jobs?page=1&limit=1", headers={"Authorization": f"Bearer {token}"})
    assert jobs.status_code == 200
    payload = jobs.json()
    assert payload["page"] == 1
    assert payload["totalPages"] == 2
    assert len(payload["jobs"]) == 1

    add_favorite = client.post(
        "/favorites",
        json={"job_url": "https://jobs.example/1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert add_favorite.status_code == 200
    assert add_favorite.json()["favorited"] is True

    favorites = client.get("/favorites", headers={"Authorization": f"Bearer {token}"})
    assert favorites.status_code == 200
    assert len(favorites.json()["favorites"]) == 1
