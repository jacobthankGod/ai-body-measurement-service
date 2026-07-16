#!/bin/bash
# Run SQL migration against Supabase database
# Usage: ./run_migration.sh [migration_file]

set -e

RUN_ALL=${RUN_ALL:-false}
MIGRATION_FILE=${1:-"scripts/004_smpl_params_migration.sql"}

if [ -z "$SUPABASE_DB_URL" ]; then
    echo "Error: SUPABASE_DB_URL environment variable not set"
    echo ""
    echo "Usage: SUPABASE_DB_URL='postgresql://...' ./scripts/run_migration.sh [migration_file]"
    echo "   or: RUN_ALL=true SUPABASE_DB_URL='...' ./scripts/run_migration.sh"
    exit 1
fi

run_sql_file() {
    local file=$1
    if [ ! -f "$file" ]; then
        echo "File not found: $file"
        return 1
    fi
    echo "Running: $file"
    psql "$SUPABASE_DB_URL" -f "$file"
    if [ $? -ne 0 ]; then
        echo "FAILED: $file"
        exit 1
    fi
    echo "OK: $file"
}

if [ "$RUN_ALL" = "true" ]; then
    echo "Running all pending migrations..."
    run_sql_file "scripts/004_smpl_params_migration.sql"
    run_sql_file "scripts/005_rls_policies.sql"
    run_sql_file "scripts/006_drafts_table.sql"
    echo "All migrations completed successfully"
else
    run_sql_file "$MIGRATION_FILE"
fi
