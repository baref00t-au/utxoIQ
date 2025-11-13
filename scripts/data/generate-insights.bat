@echo off
echo Starting AI Insight Generation...
echo.

REM Set environment variables
set GCP_PROJECT_ID=utxoiq-dev
set BIGQUERY_DATASET_INTEL=intel
set BIGQUERY_DATASET_BTC=btc
set VERTEX_AI_LOCATION=us-central1

echo Generating insights using Vertex AI Gemini...
echo.

python services\insight-generator\src\main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ Insights generated successfully!
    echo ========================================
    echo.
    echo Check BigQuery: %GCP_PROJECT_ID%.%BIGQUERY_DATASET_INTEL%.insights
    echo Test API: https://utxoiq-web-api-dev-544291059247.us-central1.run.app/insights/public
) else (
    echo.
    echo ========================================
    echo ❌ Insight generation failed!
    echo ========================================
)
