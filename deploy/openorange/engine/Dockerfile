ARG UPSTREAM
FROM ${UPSTREAM}
ARG BUILD_RECORD_SHA256
LABEL org.opencontainers.image.source=https://github.com/laputa-systems/rivet \
      systems.laputa.engine.build-record=${BUILD_RECORD_SHA256}
COPY rivet-engine /usr/bin/rivet-engine
