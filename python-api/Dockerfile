FROM python:3.13
WORKDIR /app

RUN if [ $(dpkg --print-architecture | grep arm64) ]; then \
      apt update && apt install -y build-essential cmake; \
    fi;

RUN pip install --upgrade pip
RUN pip install poetry uv

COPY . .

RUN rm -rf dist && poetry build
RUN uv pip install --system dist/*.whl

CMD ["gunicorn", "-c", "gunicorn_conf.py", "-k", "python_api.worker.UvicornWorker", "python_api.main:app"]
