ARG BASE=docker.io/library/python:3.14-alpine@sha256:5862d971d1f0ae26b258cefa4e893556b1d3aba81bd2ff30888704ad378bab67
FROM ${BASE}
ARG ENGINE_IMAGE_TAG
ENV RIVET_CONFIGURED_IMAGE_TAG=${ENGINE_IMAGE_TAG}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY server.py index.html app.js style.css /app/
USER 10001:10001
ENTRYPOINT ["python", "-I", "/app/server.py", "/run/secrets/rivet-explorer.json"]
