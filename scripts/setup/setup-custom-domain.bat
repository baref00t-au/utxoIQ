@echo off
REM Setup custom domain for Cloud Run services
REM Usage: scripts\setup-custom-domain.bat [dev|prod]

set ENV=%1
if "%ENV%"=="" set ENV=dev

if "%ENV%"=="prod" (
    set PROJECT_ID=utxoiq
    set SERVICE_NAME=utxoiq-web-api
    set DOMAIN=api.utxoiq.com
    echo Setting up PRODUCTION domain: %DOMAIN%
) else (
    set PROJECT_ID=utxoiq-dev
    set SERVICE_NAME=utxoiq-web-api-dev
    set DOMAIN=api-dev.utxoiq.com
    echo Setting up DEVELOPMENT domain: %DOMAIN%
)

echo.
set REGION=us-central1

echo Creating domain mapping...
echo.

gcloud run domain-mappings create ^
  --service %SERVICE_NAME% ^
  --domain %DOMAIN% ^
  --region %REGION% ^
  --project %PROJECT_ID%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Domain mapping failed!
    echo.
    echo Common issues:
    echo   1. Domain not verified in GCP Console
    echo   2. Service doesn't exist yet
    echo   3. Domain already mapped
    echo.
    echo To verify domain:
    echo   1. Go to: https://console.cloud.google.com/run/domains
    echo   2. Click "Verify domain"
    echo   3. Follow verification steps
    echo.
    exit /b 1
)

echo.
echo ========================================
echo Domain mapping created!
echo ========================================
echo.
echo Domain: %DOMAIN%
echo Service: %SERVICE_NAME%
echo.
echo NEXT STEPS:
echo.
echo 1. Add DNS records to your domain registrar:
echo.
echo    Type: CNAME
echo    Name: %DOMAIN:~0,-11%
echo    Value: ghs.googlehosted.com
echo.
echo    OR add A records:
echo.
echo    Type: A
echo    Name: %DOMAIN:~0,-11%
echo    Values: 216.239.32.21
echo            216.239.34.21
echo            216.239.36.21
echo            216.239.38.21
echo.
echo 2. Wait 15-60 minutes for SSL certificate provisioning
echo.
echo 3. Verify domain is working:
echo    curl https://%DOMAIN%/health
echo.
echo 4. Update frontend config:
if "%ENV%"=="prod" (
    echo    frontend\.env.production:
) else (
    echo    frontend\.env.local:
)
echo      NEXT_PUBLIC_API_URL=https://%DOMAIN%
echo      NEXT_PUBLIC_WS_URL=wss://%DOMAIN%
echo.
echo 5. Check status:
echo    gcloud run domain-mappings describe %DOMAIN% --region %REGION% --project %PROJECT_ID%
echo.
