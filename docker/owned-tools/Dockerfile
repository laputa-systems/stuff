# Owned build tools for fleet Dockerfiles; see docs/fleet.md "Acquiring owned tools".
# The fetch stage builds on the pinned musl Alpine base from
# fleet/policy/musl-toolchain.toml; the published stage is scratch plus
# /opt/laputa only, so consumers supply their own libc.
FROM alpine:3.24.2@sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6 AS fetch

ARG TARGETARCH
RUN apk add --no-cache \
        curl=8.23.0-r0 \
        ca-certificates=20261020-r0 \
        tar=1.35-r5 \
        xz=5.8.4-r0

WORKDIR /src
COPY bootstrap/ /src/bootstrap/
COPY tools.lock.json /src/tools.lock.json

RUN set -eu; \
    case "$TARGETARCH" in \
        amd64) triple=x86_64-unknown-linux-musl ;; \
        arm64) triple=aarch64-unknown-linux-musl ;; \
        *) echo "owned-tools: unsupported TARGETARCH $TARGETARCH" >&2; exit 1 ;; \
    esac; \
    export BUILDLIB_CACHE=/cache; \
    mkdir -p /cache /opt/laputa/bin; \
    for tool in cmake cpython fd git gluon jaq llvm mold rg; do \
        bindir=$(sh /src/bootstrap/buildlib-run -- -m buildlib tools install "$tool" \
            --lock /src/tools.lock.json --cache /cache --target "$triple"); \
        case "$(basename "$bindir")" in \
            bin) tree=$(dirname "$bindir"); rel=bin/ ;; \
            *) tree=$bindir; rel= ;; \
        esac; \
        mv "$tree" "/opt/laputa/$tool"; \
        newbindir="/opt/laputa/$tool/$rel"; \
        for program in "$newbindir"/*; do \
            { [ -f "$program" ] || [ -L "$program" ]; } && [ -x "$program" ] || continue; \
            ln -sfn "$program" "/opt/laputa/bin/$(basename "$program")"; \
        done; \
    done

RUN set -eu; \
    /opt/laputa/bin/git --version; \
    /opt/laputa/bin/python3 -c 'import ssl'; \
    /opt/laputa/bin/cmake --version; \
    /opt/laputa/bin/meson --version; \
    /opt/laputa/bin/ninja --version; \
    /opt/laputa/bin/clang --version; \
    /opt/laputa/bin/rg --version; \
    /opt/laputa/bin/jaq --version

FROM scratch
COPY --from=fetch /opt/laputa /opt/laputa
