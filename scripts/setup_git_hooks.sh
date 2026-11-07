#!/bin/bash
# Config

set -e

echo "================================="
echo "Git Hooks"
echo "================================="
echo ""
echo "ℹ️  : README  GitHub Actions"
echo ""

# Config
if [ ! -d ".git" ]; then
    echo ": "
    exit 1
fi

# Config
if [ ! -d ".githooks" ]; then
    echo ": .githooks"
    exit 1
fi

# Config
if [ -f ".githooks/pre-commit.disabled" ]; then
    echo " pre-commit hook"
    echo ""
    echo "README  GitHub Actions "
    echo "  - "
    echo "  - "
    echo "  -  API "
    echo ""
    read -p " pre-commit hook() [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mv .githooks/pre-commit.disabled .githooks/pre-commit
        echo "✅ Pre-commit hook "
    else
        echo "✅  GitHub Actions "
        echo ""
        echo ": uv run python scripts/translate_readme.py"
        exit 0
    fi
fi

# Config
if [ -f ".githooks/pre-commit" ]; then
    echo "Git.githooks..."
    git config core.hooksPath .githooks

    # Config
    echo "hooks..."
    chmod +x .githooks/pre-commit

    echo ""
    echo "================================="
    echo "✅ Git Hooks"
    echo "================================="
    echo ""
    echo ""
    echo "  • pre-commit: README.mdREADME_EN.md"
    echo ""
    echo ""
    echo "  - README.mdREADME_EN.md"
    echo "  - .envGOOGLE_API_KEY"
    echo "  - "
    echo "  -  30-60 "
else
    echo ""
    echo "================================="
    echo "✅  Git Hooks"
    echo "================================="
    echo ""
    echo "README  GitHub Actions "
    echo ": .githooks/README.md"
fi

echo ""
