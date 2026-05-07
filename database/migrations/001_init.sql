-- Initial schema. Source of truth lives in backend/app/models — Alembic
-- generates real migrations. This file is loaded by docker-entrypoint-initdb.d
-- on first Postgres start so the DB has tables even before the app boots.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Note: in real deploys, run `alembic upgrade head` from the backend
-- container to keep schema in sync. This SQL is a safety net for first boot.

-- Bootstrap is otherwise handled by SQLAlchemy create_all on dev startup
-- and Alembic in production.
