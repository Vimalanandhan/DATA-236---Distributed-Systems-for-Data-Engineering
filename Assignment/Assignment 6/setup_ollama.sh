#!/bin/bash

echo "Setting up Ollama for AI Memory System..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null
then
    echo "Ollama not found. Please install Ollama from https://ollama.ai/ and run this script again."
    exit 1
fi

echo "Starting Ollama service..."
ollama serve & # Run in background

# Give Ollama a moment to start
sleep 5

echo "Pulling required models..."

# Pull chat model
echo "Pulling phi3:mini model..."
ollama pull phi3:mini

# Pull embedding model
echo "Pulling nomic-embed-text model..."
ollama pull nomic-embed-text

echo "Ollama setup complete!"
echo "Models available:"
ollama list

echo ""
echo "To start the FastAPI server, run:"
echo "python3 main.py"
