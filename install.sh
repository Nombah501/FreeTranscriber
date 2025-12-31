#!/bin/bash

# FreeTranscriber Installation Script for Linux (Enhanced Version)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions for colored output
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

echo -e "${BLUE}🎙️ FreeTranscriber Installation${NC}"
echo "================================"
echo ""

# Detect display server
info "Detecting display server..."
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    echo -e "${YELLOW}Wayland detected${NC}"
    warning "Global hotkeys may not work on Wayland without additional configuration."
    warning "For full hotkey support, consider:"
    warning "  • Using X11 session, or"
    warning "  • Configuring Wayland compositor to allow input monitoring"
    read -p "Press Enter to continue..." 
elif [ "$XDG_SESSION_TYPE" = "x11" ] || [ -n "$DISPLAY" ]; then
    success "X11 detected - Global hotkeys will work correctly"
else
    warning "Unable to detect display server. Global hotkeys may not work."
fi
echo ""

# Check Python version
info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    error "Python 3 not found. Please install Python 3.10 or higher."
    echo "   On Ubuntu/Debian: sudo apt install python3"
    echo "   On Arch/Manjaro: sudo pacman -S python"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

echo "   Found Python version: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    error "Python 3.10 or higher is required. Current: $PYTHON_VERSION"
    exit 1
fi

success "Python version is compatible: $PYTHON_VERSION"
echo ""

# Check and fix pip issues
info "Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    warning "pip3 not found. Attempting to install..."
    
    if command -v apt &> /dev/null; then
        info "Installing pip via apt..."
        sudo apt update
        sudo apt install -y python3-pip
    elif command -v pacman &> /dev/null; then
        info "Installing pip via pacman..."
        sudo pacman -S --needed python-pip
    else
        error "Unknown package manager. Please install pip manually."
        exit 1
    fi
fi

# Test pip functionality
info "Testing pip functionality..."
if ! pip3 --version &> /dev/null; then
    warning "pip3 exists but has issues. Attempting to fix..."
    
    # Try to reinstall pip using python module
    info "Reinstalling pip via ensurepip..."
    python3 -m ensurepip --upgrade || true
    
    # Try using python -m pip
    if ! python3 -m pip --version &> /dev/null; then
        error "Unable to fix pip issues. Please install/reinstall pip manually."
        exit 1
    fi
    
    info "Using 'python3 -m pip' instead of 'pip3' command"
    PIP_CMD="python3 -m pip"
else
    PIP_CMD="pip3"
fi

success "pip is working correctly"
echo ""

# Configure hotkeys (udev rules and input group)
info "Configuring global hotkeys support..."

# Check if user is in input group
if groups $USER | grep -q '\binput\b'; then
    success "User is already in 'input' group"
else
    warning "User is not in 'input' group"
    info "Adding user to 'input' group for hotkey support..."
    sudo usermod -a -G input $USER
    success "User added to 'input' group"
    warning "You need to log out and log back in for group changes to take effect"
fi
echo ""

# Create udev rules for input devices
UDEV_RULES_DIR="/etc/udev/rules.d"
UDEV_RULES_FILE="$UDEV_RULES_DIR/99-freetranscriber-input.rules"

info "Setting up udev rules for input devices..."
if [ -f "$UDEV_RULES_FILE" ]; then
    success "Udev rules file already exists"
else
    info "Creating udev rules file..."
    sudo tee "$UDEV_RULES_FILE" > /dev/null <<'EOF'
# FreeTranscriber - Allow input device access for hotkeys
KERNEL=="event*", SUBSYSTEM=="input", GROUP="input", MODE="0660"
EOF
    success "Udev rules created at $UDEV_RULES_FILE"
    info "Reloading udev rules..."
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    success "Udev rules reloaded"
fi
echo ""

# Check if portaudio is installed (required by sounddevice)
info "Checking PortAudio audio library..."
if ! python3 -c "import sounddevice" 2>/dev/null; then
    warning "PortAudio/sounddevice not found. Installing system dependencies..."
    
    if command -v pacman &> /dev/null; then
        info "Installing PortAudio for Arch/Manjaro..."
        sudo pacman -S --needed portaudio python-pyaudio
    elif command -v apt &> /dev/null; then
        info "Installing PortAudio for Ubuntu/Debian..."
        sudo apt update
        sudo apt install -y python3-pyaudio portaudio19-dev
    else
        warning "Unknown package manager. Please install PortAudio manually."
        info "On Arch/Manjaro: sudo pacman -S portaudio python-pyaudio"
        info "On Ubuntu/Debian: sudo apt install python3-pyaudio portaudio19-dev"
    fi
else
    success "PortAudio is already installed"
fi
echo ""

# Install Python dependencies
info "Installing Python dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    $PIP_CMD install --user -r requirements.txt 2>&1 || {
        warning "Installation with --user failed. Trying with --break-system-packages..."
        $PIP_CMD install --break-system-packages -r requirements.txt 2>&1 || {
            error "Failed to install Python dependencies"
            exit 1
        }
    }
    success "Python dependencies installed successfully"
else
    error "requirements.txt not found in current directory"
    exit 1
fi
echo ""

# Install the package in development mode
info "Installing FreeTranscriber package..."
$PIP_CMD install --user -e . 2>&1 || {
    warning "Installation with --user failed. Trying with --break-system-packages..."
    $PIP_CMD install --break-system-packages -e . 2>&1 || {
        error "Failed to install FreeTranscriber package"
        exit 1
    }
}
success "FreeTranscriber installed successfully"
echo ""

# Create desktop entry
info "Creating desktop entry..."
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/freetranscriber.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=FreeTranscriber
Comment=AI Voice to Text Transcriber
Exec=freetranscriber
Icon=freetranscriber
Terminal=false
Categories=Utility;AudioVideo;
StartupNotify=true
EOF

success "Desktop entry created at $DESKTOP_DIR/freetranscriber.desktop"
echo ""

# Post-installation verification
info "Running post-installation checks..."

# Check if command is available
if command -v freetranscriber &> /dev/null || python3 -c "import freetranscriber" 2>/dev/null; then
    success "FreeTranscriber command is available"
else
    warning "FreeTranscriber command may not be in PATH"
    info "You may need to restart your shell or add to PATH:"
    info "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# Check if sounddevice works
if python3 -c "import sounddevice" 2>/dev/null; then
    success "Audio library (sounddevice) is working"
else
    warning "Audio library may have issues. Audio recording might not work."
fi

# Check if pynput works (for hotkeys)
if python3 -c "import pynput" 2>/dev/null; then
    success "Hotkey library (pynput) is available"
else
    warning "Hotkey library (pynput) may not be installed"
fi
echo ""

# Display summary
echo "================================"
success "Installation completed!"
echo ""
echo "📋 Summary:"
echo "  • Display server: $XDG_SESSION_TYPE (detected)"
echo "  • Python version: $PYTHON_VERSION"
echo "  • Input group: $(groups $USER | grep -q '\binput\b' && echo 'Added' || echo 'Not added - requires relogin')"
echo "  • Udev rules: Configured"
echo ""
echo "🚀 To run FreeTranscriber:"
echo "  • Command: freetranscriber"
echo "  • Or find: FreeTranscriber in application menu"
echo ""
echo "⚙️  To change settings:"
echo "  • Right-click on the icon → Settings"
echo "  • Or run: freetranscriber-setup"
echo ""
echo "📝 Important notes:"
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    warning "  • Wayland detected: Global hotkeys may not work properly"
    info "    Consider using X11 or configuring your compositor"
fi
if ! groups $USER | grep -q '\binput\b'; then
    warning "  • Log out and log back in for 'input' group to take effect"
fi
warning "  • Restart your terminal or run: source ~/.bashrc (or ~/.zshrc)"
echo ""
success "Installation complete!"
