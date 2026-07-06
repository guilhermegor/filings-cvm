#!/bin/bash
# Database lifecycle helper. Sub-commands:
#   up       Idempotently bring the DB up: start services, ensure schema, migrate.
#   backup   Dump the database to BACKUP_STORE_PATH.
#   restore  Restore the database from DUMP=<path>.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

load_env() {
	if [[ ! -f .env ]]; then
		print_status "error" ".env file not found — copy .env.example to .env and fill in the values"
		exit 1
	fi

	str_db_backend=$(_read_env_var DB_BACKEND)
	str_db_backend="${str_db_backend:-sqlite}"

	str_app_name=$(_read_env_var APP_NAME)
	str_app_name="${str_app_name:-app}"

	str_db_schema=$(_read_env_var DB_SCHEMA)
	str_db_schema="${str_db_schema:-public}"

	str_db_user=$(_read_env_var DB_USER)

	str_db_name=$(_read_env_var DB_NAME)

	str_db_password=$(_read_env_var DB_PASSWORD)

	str_db_host=$(_read_env_var DB_HOST)
	str_db_host="${str_db_host:-localhost}"

	str_db_port=$(_read_env_var DB_PORT)
	str_db_port="${str_db_port:-5432}"

	print_status "config" "Backend: $str_db_backend | Schema: $str_db_schema | DB: $str_db_name"
}

start_services() {
	if [[ ! -f docker-compose.yml ]]; then
		print_status "warning" "docker-compose.yml not found — skipping service start"
		return 0
	fi

	print_status "info" "Starting Docker services..."
	docker compose up -d
	print_status "success" "Services started"
}

ensure_schema() {
	if [[ "$str_db_backend" != "postgresql" ]]; then
		print_status "info" "Schema creation not needed for backend: $str_db_backend"
		return 0
	fi

	print_status "info" "Ensuring schema '$str_db_schema' exists..."

	local str_schema_exists
	str_schema_exists=$(PGPASSWORD="$str_db_password" psql \
		-h "$str_db_host" -p "$str_db_port" \
		-U "$str_db_user" -d "$str_db_name" \
		-tAc "SELECT 1 FROM information_schema.schemata WHERE schema_name='${str_db_schema}';" \
		2>/dev/null || echo "")

	if [[ "$str_schema_exists" == "1" ]]; then
		print_status "info" "Schema '$str_db_schema' already exists — skipping"
	else
		PGPASSWORD="$str_db_password" psql \
			-h "$str_db_host" -p "$str_db_port" \
			-U "$str_db_user" -d "$str_db_name" \
			-c "CREATE SCHEMA IF NOT EXISTS ${str_db_schema};"
		print_status "success" "Schema '$str_db_schema' created"
	fi
}

apply_migrations() {
	if [[ ! -f alembic.ini ]]; then
		print_status "warning" "alembic.ini not found — skipping migrations"
		return 0
	fi

	print_status "info" "Applying Alembic migrations..."
	export PYTHONPATH=".:src"
	# Resolve Poetry robustly (bare `poetry` may be absent; see bin/poetry_exec.sh).
	bootstrap_init
	ensure_poetry
	run_poetry run alembic upgrade head
	print_status "success" "Migrations applied"
}

backup() {
	if [[ "$str_db_backend" != "postgresql" ]]; then
		print_status "error" "Backup only supported for PostgreSQL backend"
		exit 1
	fi

	local str_backup_path
	str_backup_path=$(_read_env_var BACKUP_STORE_PATH)

	if [[ -z "$str_backup_path" ]]; then
		print_status "error" "BACKUP_STORE_PATH is not set in .env"
		exit 1
	fi

	local str_timestamp
	str_timestamp=$(date +%Y%m%d_%H%M%S)
	local str_dump_dir="$str_backup_path/dbs_bkp/$str_app_name"
	local str_dump_file="$str_dump_dir/${str_app_name}_${str_timestamp}.dump"

	mkdir -p "$str_dump_dir"
	print_status "info" "Backing up '$str_db_name' to $str_dump_file..."

	docker compose exec -T \
		-e PGPASSWORD="$str_db_password" \
		postgresql pg_dump -U "$str_db_user" -Fc "$str_db_name" >"$str_dump_file"

	print_status "success" "Backup written to $str_dump_file"
}

restore() {
	if [[ "$str_db_backend" != "postgresql" ]]; then
		print_status "error" "Restore only supported for PostgreSQL backend"
		exit 1
	fi

	local str_dump_file="${DUMP:-}"

	if [[ -z "$str_dump_file" ]]; then
		print_status "error" "Specify the dump file: DUMP=<path> make db_restore"
		exit 1
	fi

	if [[ ! -f "$str_dump_file" ]]; then
		print_status "error" "Dump file not found: $str_dump_file"
		exit 1
	fi

	print_status "info" "Restoring '$str_db_name' from $str_dump_file..."

	docker compose exec -T \
		-e PGPASSWORD="$str_db_password" \
		postgresql pg_restore -U "$str_db_user" -d "$str_db_name" \
		--clean --if-exists --no-owner -Fc <"$str_dump_file"

	print_status "success" "Restore complete"
}

main() {
	local str_cmd="${1:-up}"

	print_status "section" "Database — $str_cmd"
	load_env

	case "$str_cmd" in
	up)
		start_services
		ensure_schema
		apply_migrations
		;;
	backup)
		backup
		;;
	restore)
		restore
		;;
	*)
		print_status "error" "Unknown sub-command: $str_cmd (use: up | backup | restore)"
		exit 1
		;;
	esac
}

main "$@"
