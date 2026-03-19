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

### Step 8: Output notice 、Suammry result and finish the workflow

#### require
- `SKILLHUB_URL` - Override the default SkillHub server URL (default has beed set,you can reset with new env)
- `SKILLHUB_API_KEY` - Default API token for authentication (required for most operations,you can set in .bashrc/.zshrc/profile)


#### "command not found: skillhub.sh"

Add `~/.local/bin` to your PATH:

```bash
# For bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# For zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```
- Output the skillhub.sh requrement env key and common exception handling methods
- summary the result and status with install workflow ,succ or fail
- exit the workflow,do not other any thing