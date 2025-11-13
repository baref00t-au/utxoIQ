@echo off
echo ==========================================
echo Testing Bitcoin Core RPC Connection
echo ==========================================
echo.

REM Load credentials from .env file
for /f "tokens=1,2 delims==" %%a in (..\.env) do (
    if "%%a"=="BITCOIN_RPC_USER" set RPC_USER=%%b
    if "%%a"=="BITCOIN_RPC_PASSWORD" set RPC_PASSWORD=%%b
    if "%%a"=="BITCOIN_RPC_HOST" set RPC_HOST=%%b
    if "%%a"=="BITCOIN_RPC_PORT" set RPC_PORT=%%b
)

echo Host: %RPC_HOST%
echo Port: %RPC_PORT%
echo User: %RPC_USER%
echo ------------------------------------------
echo.

echo 1. Testing connection...
bitcoin-cli -rpcuser=%RPC_USER% -rpcpassword=%RPC_PASSWORD% -rpcconnect=%RPC_HOST% -rpcport=%RPC_PORT% getblockchaininfo
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Connection failed!
    echo.
    echo Troubleshooting:
    echo 1. Check if Bitcoin Core is running
    echo 2. Verify credentials in .env match bitcoin.conf
    echo 3. Ensure RPC is enabled in bitcoin.conf
    pause
    exit /b 1
)

echo.
echo 2. Getting block count...
bitcoin-cli -rpcuser=%RPC_USER% -rpcpassword=%RPC_PASSWORD% -rpcconnect=%RPC_HOST% -rpcport=%RPC_PORT% getblockcount

echo.
echo 3. Getting mempool info...
bitcoin-cli -rpcuser=%RPC_USER% -rpcpassword=%RPC_PASSWORD% -rpcconnect=%RPC_HOST% -rpcport=%RPC_PORT% getmempoolinfo

echo.
echo ==========================================
echo SUCCESS! Bitcoin Core connection works.
echo ==========================================
pause
