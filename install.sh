#!/bin/bash

echo "EvanAI Client Installation Script"
echo "================================"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Install package in development mode
echo "Installing evanai-client..."
pip install -e .

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.template .env
    echo "Please edit .env and add your ANTHROPIC_API_KEY"
fi

echo ""
echo "Installation complete!"
echo ""
echo "To get started:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Set your API key in .env file"
echo "3. Run the client: evanai-client run"