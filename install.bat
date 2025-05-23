@echo off
setlocal EnableDelayedExpansion

REM Set up colors for better readability
set "YELLOW=[33m"
set "GREEN=[32m"
set "RED=[31m"
set "NC=[0m"

echo %YELLOW%Checking for Python installation...%NC%
REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    python3 --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo %RED%Python 3 is required but not found.%NC%
        echo Please install Python 3 using one of these methods:
        echo   - Download from https://www.python.org/downloads/
        echo   - Or use Microsoft Store to install Python 3
        exit /b 1
    ) else (
        echo %GREEN%Python 3 found!%NC%
        set "PYTHON_CMD=python3"
    )
) else (
    REM Check if this is Python 3
    for /f "tokens=2 delims= " %%a in ('python --version 2^>^&1') do (
        set "PY_VERSION=%%a"
    )
    if "!PY_VERSION:~0,1!"=="3" (
        echo %GREEN%Python 3 found!%NC%
        set "PYTHON_CMD=python"
    ) else (
        echo %RED%Python 3 is required but not found.%NC%
        echo Please install Python 3 using one of these methods:
        echo   - Download from https://www.python.org/downloads/
        echo   - Or use Microsoft Store to install Python 3
        exit /b 1
    )
)

REM Create a virtual environment
if not exist venv (
    %PYTHON_CMD% -m virtualenv venv
    if %ERRORLEVEL% NEQ 0 (
        %PYTHON_CMD% -m venv venv
    )
)

REM Activate virtual environment and install dependencies
echo %YELLOW%Installing dependencies...%NC%
call venv\Scripts\activate
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install --upgrade certifi
%PYTHON_CMD% -m pip install docling tqdm colorama

REM Set certificate environment variables
echo %YELLOW%Setting up SSL certificates...%NC%
for /f "tokens=*" %%a in ('%PYTHON_CMD% -m certifi') do (
    set "CERT_PATH=%%a"
)

REM If zscaler.pem exists, add it to certifi
if exist zscaler.pem (
    type zscaler.pem >> !CERT_PATH!
    echo %GREEN%Added Zscaler certificate to certifi%NC%
)

echo set SSL_CERT_FILE=!CERT_PATH! >> venv\Scripts\activate.bat
echo set REQUESTS_CA_BUNDLE=!CERT_PATH! >> venv\Scripts\activate.bat

REM Download models ahead of time
echo %YELLOW%Downloading Docling models...%NC%
docling-tools models download
if %ERRORLEVEL% NEQ 0 (
    echo %RED%Failed to download models with docling-tools. Trying alternative method...%NC%
    %PYTHON_CMD% -c "try: from docling.utils.model_downloader import download_models; print('Downloading models, please wait...'); download_models(show_progress=True); print('Models downloaded successfully!'); except ImportError as e: print(f'Error importing Docling: {e}'); except Exception as e: print(f'Error downloading models: {e}')"
)

echo %GREEN%Setup complete!%NC%
echo To use the script, first activate the virtual environment:
echo   %YELLOW%call venv\Scripts\activate%NC%
echo Then run:
echo   %YELLOW%python textmify.py [folder]%NC%
pause