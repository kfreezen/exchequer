import pytest

from python_api.repositories import Repository, compatibility_please
from python_api.models import CamelModel

from fastapi import FastAPI, Depends, Header
from fastapi.testclient import TestClient


class SampleModel(CamelModel):
    sample: str = ""

    def to_user(self, app_platform, app_build):
        if app_platform == "Apple" and int(app_build) <= 30:
            self.sample = "TEST"
        return self


class SampleRepository(Repository):
    def __init__(self, app_platform, app_build):
        super().__init__(app_platform, app_build)

    @compatibility_please
    async def sample_method(self) -> SampleModel:
        return SampleModel(sample="sample")

    @compatibility_please
    async def sample_list_method(self) -> list[SampleModel]:
        return [SampleModel(sample="sample")]


app = FastAPI()


def sample_repo(
    x_app_build: int | None = Header(None), x_app_platform: str | None = Header(None)
):
    return SampleRepository(x_app_platform, x_app_build)


@app.get("/")
async def root(repo: SampleRepository = Depends(sample_repo)):
    return await repo.sample_method()


@pytest.mark.parametrize(
    "app_platform, app_build, expected",
    [
        ("Apple", 30, "TEST"),
        ("Apple", 28, "TEST"),
        ("Apple", 31, "sample"),
        ("Android", 30, "sample"),
        ("Android", 31, "sample"),
        (None, None, "sample"),
    ],
)
@pytest.mark.asyncio
async def test_sample_repository(app_platform, app_build, expected):
    repo = SampleRepository(app_platform, app_build)
    model = await repo.sample_method()
    assert model.sample == expected


@pytest.mark.asyncio
async def test_sample_list_method():
    repo = SampleRepository("Apple", 30)
    models = await repo.sample_list_method()
    assert models[0].sample == "TEST"


@pytest.mark.parametrize(
    "app_platform, app_build, expected",
    [
        ("Apple", 30, "TEST"),
        ("Apple", 28, "TEST"),
        ("Apple", 31, "sample"),
        ("Android", 30, "sample"),
        ("Android", 31, "sample"),
        (None, None, "sample"),
    ],
)
def test_sample_repository_in_fastapi(app_platform, app_build, expected):
    with TestClient(app) as client:
        headers = {}
        if app_platform:
            headers["x-app-platform"] = app_platform
        if app_build:
            headers["x-app-build"] = str(app_build)

        response = client.get("/", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"sample": expected}
