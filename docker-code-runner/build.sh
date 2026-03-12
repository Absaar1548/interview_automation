#!/bin/bash
set -e

echo "Building Docker images for code execution..."

echo "  [1/4] Building Python runner..."
docker build -f Dockerfile.python -t code-runner-python .

echo "  [2/4] Building JavaScript runner..."
docker build -f Dockerfile.javascript -t code-runner-javascript .

echo "  [3/4] Building Java runner..."
docker build -f Dockerfile.java -t code-runner-java .

echo "  [4/4] Building C++ runner..."
docker build -f Dockerfile.cpp -t code-runner-cpp .

echo ""
echo "All images built successfully!"
docker images | grep code-runner
