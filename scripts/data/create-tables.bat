@echo off
echo Creating database tables in Cloud SQL...
echo.

REM Read the SQL file content
set SQL_FILE=scripts\create-tables.sql

echo Executing SQL script via gcloud...
echo.

gcloud sql databases patch utxoiq ^
  --instance=utxoiq-db-dev ^
  --project=utxoiq-dev

echo.
echo ========================================
echo To create tables, run this command in Cloud Shell:
echo ========================================
echo.
echo gcloud sql connect utxoiq-db-dev --user=postgres --database=utxoiq --project=utxoiq-dev
echo.
echo Then paste the contents of scripts/create-tables.sql
echo.
echo Or upload the file and run:
echo psql -U postgres -d utxoiq -f create-tables.sql
echo.
