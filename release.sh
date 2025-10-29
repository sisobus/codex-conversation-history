#!/bin/bash

# cohistory Release Script
# Usage: ./release.sh <version> [commit message]
# Example: ./release.sh 1.0.0 "Add Codex session browser"

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
HOMEBREW_TAP_PATH="../homebrew-tap"
FORMULA_RELATIVE_PATH="Formula/cohistory.rb"
FORMULA_FILE="$HOMEBREW_TAP_PATH/$FORMULA_RELATIVE_PATH"
SCRIPT_NAME="cohistory.py"
REPO_NAME="codex-conversation-history"
GITHUB_USER="sisobus"

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}========================================${NC}"
    echo -e "${CYAN}${BOLD}      cohistory Release Script         ${NC}"
    echo -e "${CYAN}${BOLD}========================================${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}→ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ Error: $1${NC}"
    exit 1
}

print_warning() {
    echo -e "${YELLOW}⚠ Warning: $1${NC}"
}

if [ -z "$1" ]; then
    print_error "Version number required!"
    echo "Usage: $0 <version> [commit message]"
    echo "Example: $0 1.0.0 \"Add Codex session browser\""
    exit 1
fi

VERSION=$1
COMMIT_MESSAGE=${2:-"Release v$VERSION"}

if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_error "Invalid version format. Use semantic versioning (e.g., 1.0.0)"
fi

print_header

print_step "Checking prerequisites..."

if [ ! -f "$SCRIPT_NAME" ]; then
    print_error "Must be run from $REPO_NAME directory"
fi

if [ ! -d "$HOMEBREW_TAP_PATH" ]; then
    print_error "homebrew-tap not found at $HOMEBREW_TAP_PATH"
fi

if [ ! -f "$FORMULA_FILE" ]; then
    print_error "Formula file not found at $FORMULA_FILE. Please create it first in the homebrew-tap repository."
fi

if [ -n "$(git status --porcelain)" ]; then
    print_warning "You have uncommitted changes in $REPO_NAME"
    read -p "Do you want to continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

if [ -n "$(cd $HOMEBREW_TAP_PATH && git status --porcelain)" ]; then
    print_warning "You have uncommitted changes in homebrew-tap"
    read -p "Do you want to continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_success "Prerequisites checked"
echo ""

print_step "Updating version in $SCRIPT_NAME to $VERSION..."
sed -i '' "s/^VERSION = \".*\"$/VERSION = \"$VERSION\"/" "$SCRIPT_NAME"
print_success "Updated version in $SCRIPT_NAME"

print_step "Committing changes..."
git add "$SCRIPT_NAME"
git commit -m "$COMMIT_MESSAGE" || {
    print_warning "No changes to commit (version might already be $VERSION)"
}

print_step "Pushing to master..."
git push origin master || git push origin main
print_success "Pushed to repository"

print_step "Creating tag v$VERSION..."
git tag -a "v$VERSION" -m "$COMMIT_MESSAGE"

print_step "Pushing tag..."
git push origin "v$VERSION"
print_success "Tag v$VERSION created and pushed"

print_step "Waiting for GitHub to process the tag..."
sleep 3

print_step "Calculating SHA256 for release tarball..."
TARBALL_URL="https://github.com/$GITHUB_USER/$REPO_NAME/archive/refs/tags/v$VERSION.tar.gz"
SHA256=$(curl -sL "$TARBALL_URL" | shasum -a 256 | cut -d' ' -f1)

if [ -z "$SHA256" ] || [ "$SHA256" = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" ]; then
    print_warning "Failed to calculate SHA256 (tarball might not be ready yet)"
    print_step "Retrying in 5 seconds..."
    sleep 5
    SHA256=$(curl -sL "$TARBALL_URL" | shasum -a 256 | cut -d' ' -f1)

    if [ -z "$SHA256" ] || [ "$SHA256" = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" ]; then
        print_error "Failed to calculate SHA256. Please check if the release was created on GitHub."
    fi
fi

print_success "SHA256: $SHA256"

print_step "Updating homebrew-tap formula..."

cd "$HOMEBREW_TAP_PATH"

sed -i '' "s|url \"https://github.com/$GITHUB_USER/$REPO_NAME/archive/refs/tags/v.*\\.tar\\.gz\"|url \"$TARBALL_URL\"|" "$FORMULA_RELATIVE_PATH"
sed -i '' "s|sha256 \"[a-f0-9]*\"|sha256 \"$SHA256\"|" "$FORMULA_RELATIVE_PATH"
sed -i '' "s|version \".*\"|version \"$VERSION\"|" "$FORMULA_RELATIVE_PATH"

print_success "Formula updated"

print_step "Committing homebrew-tap changes..."
git add "$FORMULA_RELATIVE_PATH"
git commit -m "Update cohistory to v$VERSION

$COMMIT_MESSAGE"

print_step "Pushing homebrew-tap..."
git push origin master || git push origin main
print_success "homebrew-tap updated"

cd - > /dev/null

echo ""
echo -e "${GREEN}${BOLD}========================================${NC}"
echo -e "${GREEN}${BOLD}        Release v$VERSION Complete!     ${NC}"
echo -e "${GREEN}${BOLD}========================================${NC}"
echo ""
echo -e "${CYAN}Users can now install/update with:${NC}"
echo "  brew update"
echo "  brew upgrade cohistory"
echo ""
echo -e "${CYAN}Or fresh install:${NC}"
echo "  brew tap sisobus/tap"
echo "  brew install cohistory"
echo ""
echo -e "${CYAN}Verify the new version:${NC}"
echo "  cohistory --version  # Should show: cohistory version $VERSION"
echo ""
echo -e "${CYAN}GitHub Release:${NC}"
echo "  https://github.com/$GITHUB_USER/$REPO_NAME/releases/tag/v$VERSION"
echo ""
