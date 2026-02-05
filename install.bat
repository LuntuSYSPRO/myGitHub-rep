@echo off
REM SYSPRO T900 Testing Plugin - Installation Script
REM Run this script as Administrator or ensure you have write permissions

echo ============================================
echo SYSPRO T900 Testing Plugin Installer
echo ============================================
echo.

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ and add it to your PATH
    pause
    exit /b 1
)

echo [1/4] Installing SYSPRO MCP dependencies...
cd /d "%~dp0servers\syspro-enet"
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install SYSPRO MCP dependencies
    pause
    exit /b 1
)
echo      Done.
echo.

echo [2/4] Installing MSSQL MCP server...
pip install mssql-mcp-server
if errorlevel 1 (
    echo ERROR: Failed to install mssql-mcp-server
    pause
    exit /b 1
)
echo      Done.
echo.

echo [3/4] Checking environment variables...
if "%SYSPRO_BASE_URL%"=="" (
    echo WARNING: SYSPRO_BASE_URL is not set
    echo You need to set the following environment variables:
    echo   - SYSPRO_BASE_URL
    echo   - SYSPRO_OPERATOR
    echo   - SYSPRO_PASSWORD
    echo   - SYSPRO_COMPANY_ID
    echo   - MSSQL_HOST
    echo   - MSSQL_DATABASE
    echo.
    echo Example PowerShell commands to set them:
    echo   [Environment]::SetEnvironmentVariable("SYSPRO_BASE_URL", "http://server:port/SYSPROWCFService/Rest", "User")
    echo.
) else (
    echo      Environment variables detected.
)
echo.

echo [4/4] Installation complete!
echo.
echo ============================================
echo NEXT STEPS:
echo ============================================
echo.
echo 1. Set environment variables (if not already done):
echo    - SYSPRO_BASE_URL, SYSPRO_OPERATOR, SYSPRO_PASSWORD
echo    - SYSPRO_COMPANY_ID, MSSQL_HOST, MSSQL_DATABASE
echo.
echo 2. (Optional) Run SetupSearchEntity.sql in your SysproDb
echo    to enable entity search by name.
echo.
echo 3. Install the plugin in Claude Code:
echo    claude plugin install "%~dp0" --scope user
echo.
echo 4. Restart Claude Code to load the MCP servers.
echo.
echo 5. Use /Jenkins-testcase-creator to create test cases!
echo.
echo ============================================
pause
