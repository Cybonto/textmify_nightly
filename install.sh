#!/bin/bash

# Set up colors for better readability
YELLOW="\033[1;33m"
GREEN="\033[0;32m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# Check if Python is installed
echo -e "${YELLOW}Checking for Python installation...${NC}"
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}Python 3 found!${NC}"
elif command -v python &>/dev/null; then
    # Check if this is Python 3
    PY_VERSION=$(python --version 2>&1)
    if [[ $PY_VERSION == *"Python 3"* ]]; then
        PYTHON_CMD="python"
        echo -e "${GREEN}Python 3 found!${NC}"
    else
        echo -e "${RED}Python 3 is required but not found.${NC}"
        echo -e "Please install Python 3 using one of these methods:"
        echo -e "  - macOS: brew install python3"
        echo -e "  - Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
        echo -e "  - Fedora: sudo dnf install python3 python3-pip"
        echo -e "  - Or download from https://www.python.org/downloads/"
        exit 1
    fi
else
    echo -e "${RED}Python 3 is required but not found.${NC}"
    echo -e "Please install Python 3 using one of these methods:"
    echo -e "  - macOS: brew install python3"
    echo -e "  - Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
    echo -e "  - Fedora: sudo dnf install python3 python3-pip"
    echo -e "  - Or download from https://www.python.org/downloads/"
    exit 1
fi

# Create a virtual environment
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m virtualenv venv
fi

# Determine activation script based on shell
if [[ "$SHELL" == *"zsh"* ]]; then
    ACTIVATE_CMD="source venv/bin/activate"
else
    ACTIVATE_CMD="source venv/bin/activate"
fi

# Activate virtual environment and install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
$ACTIVATE_CMD 2>/dev/null || source venv/bin/activate
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install --upgrade certifi
$PYTHON_CMD -m pip install docling tqdm colorama

# Set certificate environment variables
echo -e "${YELLOW}Setting up SSL certificates...${NC}"
cat zscaler.pem >> $(python -m certifi) #add zscaler cert to certifi
CERT_PATH=$($PYTHON_CMD -m certifi)
export SSL_CERT_FILE=${CERT_PATH}
export REQUESTS_CA_BUNDLE=${CERT_PATH}
echo "SSL_CERT_FILE=${CERT_PATH}" >> venv/bin/activate
echo "REQUESTS_CA_BUNDLE=${CERT_PATH}" >> venv/bin/activate
echo "export SSL_CERT_FILE REQUESTS_CA_BUNDLE" >> venv/bin/activate

# Download models ahead of time
echo -e "${YELLOW}Downloading Docling models...${NC}"
docling-tools models download

# Make the translator script executable
chmod +x textmify.py

echo -e "${GREEN}Setup complete!${NC}"
echo -e "To use the script, first activate the virtual environment:"
echo -e "  ${YELLOW}$ACTIVATE_CMD${NC}"
echo -e "Then run:"
echo -e "  ${YELLOW}./textmify.py [folder]${NC}"