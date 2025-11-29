import uvicorn.workers


class UvicornWorker(uvicorn.workers.UvicornWorker):
    CONFIG_KWARGS = {"root_path": ""}
