# syntax=docker/dockerfile:1
FROM alpine:3.20 AS build
COPY --from=oci.fixture/owned-tools@sha256:1111111111111111111111111111111111111111111111111111111111111111 /opt/laputa /opt/laputa
ENV PATH=/opt/laputa/bin:$PATH
RUN apk add --no-cache \
    curl
RUN make deps

FROM alpine:3.20 AS runtime
COPY --from=oci.fixture/owned-tools@sha256:1111111111111111111111111111111111111111111111111111111111111111 /opt/laputa /opt/laputa
ENV PATH=/opt/laputa/bin:$PATH

FROM debian:bookworm-slim AS apt-tools
RUN apt-get update && apt-get install -y --no-install-recommends git cmake

FROM alpine:3.20 AS python
RUN apk add --no-cache python3=3.12.9-r0 py3-pip curl
