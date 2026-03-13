# SkillHub CLI Installation Guide

This guide is for AI agents to install the SkillHub CLI tool (`skillhub.sh`) on a system.

## Overview

The SkillHub CLI is a command-line interface for interacting with SkillHub gateway resources. It supports three resource types: third-party APIs, gateway resources, and MCP servers.

## Installation Steps

### Step 1: Check if `skillhub.sh` is already installed

First, verify if the CLI tool is already installed and accessible in the PATH:

```bash
# Check if skillhub.sh command exists
if command -v skillhub.sh &> /dev/null; then
    echo "skillhub.sh is already installed at: $(which skillhub.sh)"
    echo "Current version:"
    skillhub.sh -h
    exit 0
fi

# Also check common installation locations
if [ -f "$HOME/.local/bin/skillhub.sh" ]; then
    echo "skillhub.sh found at ~/.local/bin/skillhub.sh but not in PATH"
    echo "You may need to add ~/.local/bin to your PATH"
fi
```

### Step 2: Ensure the installation directory exists

The CLI tool should be installed in `~/.local/bin`. Create this directory if it doesn't exist:

```bash
mkdir -p "$HOME/.local/bin"
```

### Step 3: Verify the SkillHub server is running

**SKILLHUB_SERVER="{SKILLHUB_URL}"**
Before downloading, ensure the SkillHub server is accessible:


```bash
# Check if server is reachable
if ! curl -s -f "$SKILLHUB_SERVER/api/v1/script/health/" > /dev/null 2>&1; then
    echo "Error: Cannot reach SkillHub server at $SKILLHUB_SERVER"
    echo "Please ensure the server is running:"
    echo "  cd backend && python main.py"
    exit 1
fi
```

### Step 4: Download the skillhub.sh script

Download the CLI tool from the SkillHub server:

```bash
INSTALL_PATH="$HOME/.local/bin/skillhub.sh"

echo "Downloading skillhub.sh from $SKILLHUB_SERVER/api/v1/script/bash..."
curl -s -f "$SKILLHUB_SERVER/api/v1/script/bash" -o "$INSTALL_PATH"

if [ $? -ne 0 ]; then
    echo "Error: Failed to download skillhub.sh"
    exit 1
fi
```

### Step 5: Make the script executable

Set execute permissions on the downloaded script:

```bash
chmod +x "$INSTALL_PATH"
echo "Made skillhub.sh executable"
```

### Step 6: Verify the installation

Run the help command to verify the installation was successful:

```bash
echo "Verifying installation..."
"$INSTALL_PATH" -h

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ SkillHub CLI installed successfully!"
    echo ""
    echo "Installation location: $INSTALL_PATH"
    echo ""
    echo "IMPORTANT: Add ~/.local/bin to your PATH if not already present:"
    echo ""
    echo "  # For bash (add to ~/.bashrc or ~/.bash_profile):"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "  # For zsh (add to ~/.zshrc):"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "  # Then reload your shell configuration:"
    echo "  source ~/.bashrc  # or source ~/.zshrc for zsh"
    echo ""
else
    echo "Error: Installation verification failed"
    exit 1
fi
```

### Step 7: Install skillhub skill
```bash
"$INSTALL_PATH" install skillhub
```

## Complete Installation Script

Here's a complete script that combines all steps:

```bash
#!/bin/bash

# SkillHub CLI Installation Script
# Run this script to install skillhub.sh on your system

set -e  # Exit on error


INSTALL_PATH="$HOME/.local/bin/skillhub.sh"

echo "=== SkillHub CLI Installation ==="
echo ""

# Step 1: Check if already installed
if command -v skillhub.sh &> /dev/null; then
    echo "✓ skillhub.sh is already installed at: $(which skillhub.sh)"
    echo "Showing help:"
    skillhub.sh -h
    exit 0
fi

# Step 2: Create installation directory
echo "→ Creating installation directory..."
mkdir -p "$HOME/.local/bin"

# Step 3: Verify server is reachable
echo "→ Checking SkillHub server at $SKILLHUB_SERVER..."
if ! curl -s -f "$SKILLHUB_SERVER/api/v1/script/health/" > /dev/null 2>&1; then
    echo "✗ Error: Cannot reach SkillHub server at $SKILLHUB_SERVER"
    echo "Please ensure the server is running:"
    echo "  cd backend && python main.py"
    exit 1
fi

# Step 4: Download the script
echo "→ Downloading skillhub.sh..."
curl -s -f "$SKILLHUB_SERVER/api/v1/script/bash" -o "$INSTALL_PATH"

if [ $? -ne 0 ]; then
    echo "✗ Error: Failed to download skillhub.sh"
    exit 1
fi

# Step 5: Make executable
echo "→ Making script executable..."
chmod +x "$INSTALL_PATH"

# Step 6: Verify installation
echo "→ Verifying installation..."
if "$INSTALL_PATH" -h > /dev/null 2>&1; then
    echo ""
    echo "=== Installation Successful ==="
    echo ""
    echo "Location: $INSTALL_PATH"
    echo ""
    echo "Next steps:"
    echo "1. Add ~/.local/bin to your PATH (if not already):"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "2. Reload your shell or run:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "3. Verify:"
    echo "   skillhub.sh -h"
    echo ""

    # Step 7: Install skillhub skill if installed successfully
    "$INSTALL_PATH" install skillhub
else
    echo "✗ Error: Installation verification failed"
    exit 1
fi
```

## Usage Examples

After installation, you can use the CLI tool:

```bash
# List all skills
skillhub.sh list

# Install a skill
skillhub.sh install weather-skill

# Call a third-party API
skillhub.sh third weather-api -method GET -inputs '{"city":"Beijing"}'

# Call a gateway resource
skillhub.sh gateway my-api -method GET -path users/123

# Call an MCP server
skillhub.sh mcp my-mcp-server -mcptool test
```

## Environment Variables

### Check and Configure SKILLHUB_API_KEY

The `SKILLHUB_API_KEY` is required for authenticating with the SkillHub server. Check if it exists:

```bash
# Check if SKILLHUB_API_KEY is set
if [ -z "$SKILLHUB_API_KEY" ]; then
    echo "⚠️  Warning: SKILLHUB_API_KEY is not set"
    echo ""
    echo "To use the SkillHub CLI, you need an API key. Choose one of the following:"
    echo ""
    echo "Option 1: Create an API key on the SkillHub server"
    echo "  1. Login to SkillHub web interface"
    echo "  2. Navigate to API Keys management"
    echo "  3. Create a new API key"
    echo "  4. Copy the key and add to your environment:"
    echo ""
    echo "     # For bash (add to ~/.bashrc or ~/.bash_profile):"
    echo "     export SKILLHUB_API_KEY='your-api-key-here'"
    echo ""
    echo "     # For zsh (add to ~/.zshrc):"
    echo "     export SKILLHUB_API_KEY='your-api-key-here'"
    echo ""
    echo "     # For openclaw (add to ~/.openclaw/openclaw.json):"
    echo "     add the key to your openclaw config:"
    echo ""
    echo "     # Then reload your shell:"
    echo "     source ~/.bashrc  # or source ~/.zshrc for zsh"
    echo ""
    echo "Option 2: Provide the key directly to AI"
    echo "  Simply share your API key with the AI agent, and it will use the -token option:"
    echo "  skillhub.sh list -token 'your-api-key-here'"
    echo "  or ask the AI export and save the key for you:"
    echo ""
else
    echo "✓ SKILLHUB_API_KEY is configured"
fi
```

### Available Environment Variables

- `SKILLHUB_URL` - Override the default SkillHub server URL (default: http://localhost:8000)
- `SKILLHUB_API_KEY` - Default API token for authentication (required for most operations)

## Troubleshooting

### "command not found: skillhub.sh"

Add `~/.local/bin` to your PATH:

```bash
# For bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# For zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```