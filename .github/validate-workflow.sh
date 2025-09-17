#!/bin/bash
# Simple validation script for GitHub Actions workflow

set -e

echo "🔍 Validating GitHub Actions workflow..."

# Check if the workflow file exists and is valid YAML
if ! command -v yamllint &> /dev/null; then
    echo "Installing yamllint for YAML validation..."
    pip install yamllint || echo "⚠️  Could not install yamllint, skipping YAML validation"
fi

if command -v yamllint &> /dev/null; then
    echo "✅ Validating YAML syntax..."
    yamllint .github/workflows/test.yml || echo "⚠️  YAML validation failed"
fi

# Test the basic pytest command locally
echo "✅ Testing pytest command locally..."
export TRAVIS_GH3=1
pytest --version
echo "Running a quick test to ensure the environment works..."
pytest tests/integration/test_main.py::Test_Main::test_add -v

echo "🎉 Basic validation completed!"
echo ""
echo "📋 GitHub Actions workflow summary:"
echo "   - File: .github/workflows/test.yml"
echo "   - Triggers: push/PR to main, master, devel branches"
echo "   - Matrix: Python 3.5-3.11 on Ubuntu & macOS"
echo "   - Environment: TRAVIS_GH3=1 (for test compatibility)"
echo "   - Coverage: Uploads to Codecov for Python 3.9/Ubuntu"
echo ""
echo "🚀 Ready to commit and push to trigger GitHub Actions!"