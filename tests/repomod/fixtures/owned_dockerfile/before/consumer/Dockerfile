# syntax=docker/dockerfile:1
FROM alpine:3.20 AS build
RUN apk add --no-cache \
    git=2.45.2-r0 cmake=3.28.3-r0 curl
RUN apk add --no-cache meson ninja-build samurai
RUN make deps && apk add mold

FROM alpine:3.20 AS runtime
COPY --from=oci.fixture/owned-tools@sha256:0000000000000000000000000000000000000000000000000000000000000000 /opt/laputa /opt/laputa
ENV PATH=/opt/laputa/bin:$PATH
RUN apk add --no-cache git fd ripgrep

FROM debian:bookworm-slim AS apt-tools
RUN apt-get update && apt-get install -y --no-install-recommends git cmake

FROM alpine:3.20 AS python
RUN apk add --no-cache python3=3.12.9-r0 py3-pip curl
