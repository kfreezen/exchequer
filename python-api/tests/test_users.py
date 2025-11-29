import uuid

from fastapi.testclient import TestClient

from python_api.models.users import DbUser


def test_get_users(test_client: TestClient, test_data):
    response = test_client.get("/admin/users")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


def test_get_user(test_client: TestClient, test_user: DbUser, test_data):
    response = test_client.get(f"/admin/users/{test_user.id}")
    assert response.status_code == 200
    assert response.json()["id"] == test_user.id
    assert response.json()["email"] == test_user.email


def test_get_nonexistent_user(test_client: TestClient, test_data):
    uid = uuid.uuid4()

    response = test_client.get(f"/admin/users/{uid}")
    assert response.status_code == 404


def test_update_user(test_client: TestClient, test_user: DbUser, test_data):
    response = test_client.put(
        f"/admin/users/{test_user.id}",
        json={
            **test_user.model_dump(mode="json", by_alias=True),
            "roles": ["user", "admin"],
        },
    )

    assert response.status_code == 200
    response = test_client.get(f"/admin/users/{test_user.id}")
    assert response.status_code == 200
    assert response.json()["roles"] == ["user", "admin"]


async def test_password_reset(
    test_client: TestClient, test_user: DbUser, test_data, postgres_conn
):
    response = test_client.get(
        "/password-reset?email=" + test_user.email,
    )

    assert response.status_code == 200
    async with postgres_conn.cursor() as cur:
        await cur.execute(
            "SELECT code FROM password_reset WHERE user_id = %s ORDER BY expires_at DESC LIMIT 1",
            (test_user.id,),
        )

        code = await cur.fetchone()
        assert code is not None

    response = test_client.post(
        "/password-reset",
        json={
            "email": test_user.email,
            "code": code["code"],
            "password": "changedpassword",
        },
    )

    assert response.status_code == 200

    response = test_client.post(
        "/login",
        data={"username": test_user.email, "password": "changedpassword"},
    )

    assert response.status_code == 200


async def test_update_password(test_client: TestClient, test_user: DbUser, test_data):
    response = test_client.put(
        f"/users/{test_user.id}/password",
        json={"oldPassword": "changedpassword", "newPassword": "newpassword"},
    )

    assert response.status_code == 200

    response = test_client.post(
        "/login",
        data={"username": test_user.email, "password": "newpassword"},
    )

    assert response.status_code == 200

    response = test_client.post(
        "/login",
        data={"username": test_user.email, "password": "password"},
    )

    assert response.status_code == 401


def test_valid_jwt(test_client: TestClient, test_user: DbUser, test_data):
    response = test_client.post(
        "/login",
        data={"username": test_user.email, "password": "newpassword"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()

    token = response.json()["access_token"]
    response = test_client.get(
        "/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
