FROM node:22-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY vite.config.ts tsconfig.json ./
COPY frontend ./frontend
RUN npm run build

FROM python:3.14-slim
LABEL org.opencontainers.image.source=https://github.com/josephburgess/gesso
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /bin/uv
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
COPY --from=frontend /app/frontend/dist ./frontend/dist
RUN DEBUG=false SECRET_KEY=collectstatic DATABASE_URL=sqlite:////tmp/collectstatic.db python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "--access-logfile", "-"]
