FROM docker.io/library/node:26.13.1-bookworm-slim@sha256:5df79989ed685e09f0a98019db4cebfb22fb9df1a53c0161664a011f7ff6b0f1
WORKDIR /app
COPY --chmod=0444 main.mjs /app/main.mjs
USER 10001:10001
CMD ["node", "/app/main.mjs"]
