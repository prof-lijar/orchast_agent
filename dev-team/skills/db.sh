#!/usr/bin/env bash
# SKILL_NAME="db"
# SKILL_DESC="Database management — SQLite, PostgreSQL, migrations"
# SKILL_VERSION="1.0.0"
# SKILL_REQUIRES=""
# SKILL_COMMANDS="sqlite_query,sqlite_schema,pg_query,pg_schema,migrate_create,migrate_run"

set -euo pipefail
REPO_DIR="${SKILL_REPO_DIR:-.}"

cmd_sqlite_query() {
    local db="${1:?Database path required}"
    local query="${2:?SQL query required}"
    sqlite3 -header -column "$REPO_DIR/$db" "$query"
}

cmd_sqlite_schema() {
    local db="${1:?Database path required}"
    sqlite3 "$REPO_DIR/$db" ".schema"
}

cmd_pg_query() {
    local query="${1:?SQL query required}"
    local conn="${2:-$DATABASE_URL}"
    if [[ -z "$conn" ]]; then
        echo "Error: No connection string. Set DATABASE_URL or pass as second argument."
        exit 1
    fi
    psql "$conn" -c "$query"
}

cmd_pg_schema() {
    local conn="${1:-$DATABASE_URL}"
    if [[ -z "$conn" ]]; then
        echo "Error: No connection string. Set DATABASE_URL or pass as first argument."
        exit 1
    fi
    psql "$conn" -c "\dt" -c "\d+"
}

cmd_migrate_create() {
    cd "$REPO_DIR"
    local name="${1:?Migration name required}"
    local tool="${2:-}"

    if [[ -n "$tool" ]]; then
        case "$tool" in
            alembic) alembic revision --autogenerate -m "$name" ;;
            prisma)  npx prisma migrate dev --name "$name" ;;
            knex)    npx knex migrate:make "$name" ;;
            goose)   goose create "$name" sql ;;
            *)       echo "Unknown migration tool: $tool" && exit 1 ;;
        esac
        return
    fi

    if [[ -f "alembic.ini" ]]; then
        alembic revision --autogenerate -m "$name"
    elif [[ -f "prisma/schema.prisma" ]]; then
        npx prisma migrate dev --name "$name"
    elif [[ -f "knexfile.js" ]] || [[ -f "knexfile.ts" ]]; then
        npx knex migrate:make "$name"
    else
        local dir="migrations"
        mkdir -p "$dir"
        local ts
        ts=$(date +%Y%m%d%H%M%S)
        local file="$dir/${ts}_${name}.sql"
        cat > "$file" <<SQL
-- Migration: $name
-- Created: $(date -Iseconds)

-- UP
BEGIN;

-- Add your migration SQL here

COMMIT;

-- DOWN (manual rollback)
-- BEGIN;
-- COMMIT;
SQL
        echo "Created migration: $file"
    fi
}

cmd_migrate_run() {
    cd "$REPO_DIR"
    local tool="${1:-}"

    if [[ -n "$tool" ]]; then
        case "$tool" in
            alembic) alembic upgrade head ;;
            prisma)  npx prisma migrate deploy ;;
            knex)    npx knex migrate:latest ;;
            goose)   goose up ;;
            *)       echo "Unknown migration tool: $tool" && exit 1 ;;
        esac
        return
    fi

    if [[ -f "alembic.ini" ]]; then
        alembic upgrade head
    elif [[ -f "prisma/schema.prisma" ]]; then
        npx prisma migrate deploy
    elif [[ -f "knexfile.js" ]] || [[ -f "knexfile.ts" ]]; then
        npx knex migrate:latest
    else
        echo "No migration tool detected. Specify tool as argument: alembic, prisma, knex, goose"
        exit 1
    fi
}

"cmd_${1}" "${@:2}"
