#!/bin/bash

# FreeTranscriber Installation Script for Linux

set -e

echo "🎙️ FreeTranscriber Installation"
echo "================================"
echo ""

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

echo "✅ Python version: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "❌ Python 3.10 or higher is required. Current: $PYTHON_VERSION"
    exit 1
fi

# Check if pip is available
echo ""
echo "📦 Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install pip."
    echo "   On Ubuntu/Debian: sudo apt install python3-pip"
    echo "   On Arch/Manjaro: sudo pacman -S python-pip"
    exit 1
fi
echo "✅ pip found"

# Check if portaudio is installed (required by sounddevice)
echo ""
echo "🔊 Checking PortAudio..."
if ! python3 -c "import sounddevice" 2>/dev/null; then
    echo "⚠️  sounddevice not found. Installing system dependencies..."
    
    if command -v pacman &> /dev/null; then
        # Arch/Manjaro
        echo "   Installing PortAudio for Arch/Manjaro..."
        sudo pacman -S --needed portaudio python-pyaudio
    elif command -v apt &> /dev/null; then
        # Ubuntu/Debian
        echo "   Installing PortAudio for Ubuntu/Debian..."
        sudo apt install -y python3-pyaudio portaudio19-dev
    else
        echo "⚠️  Unknown package manager. Please install PortAudio manually."
        echo "   On Arch/Manjaro: sudo pacman -S portaudio python-pyaudio"
        echo "   On Ubuntu/Debian: sudo apt install python3-pyaudio portaudio19-dev"
    fi
else
    echo "✅ PortAudio already installed"
fi

# Install Python dependencies
echo ""
echo "📚 Installing Python dependencies..."
pip3 install --user -r requirements.txt || {
    echo "⚠️  Trying with --break-system-packages..."
    pip3 install --break-system-packages -r requirements.txt
}

# Install the package in development mode
echo ""
echo "🔧 Installing FreeTranscriber..."
pip3 install --user -e . || {
    echo "⚠️  Trying with --break-system-packages..."
    pip3 install --break-system-packages -e .
}

# Create desktop entry
echo ""
echo "🖥️  Creating desktop entry..."
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
EOF

echo "✅ Desktop entry created at $DESKTOP_DIR/freetranscriber.desktop"

# Run setup wizard
echo ""
echo "🎯 Running setup wizard..."
echo ""
python3 -m setup_wizard

echo ""
echo "================================"
echo "✅ Installation completed!"
echo ""
echo "To run FreeTranscriber:"
echo "  • Command: freetranscriber"
echo "  • Or click: FreeTranscriber in application menu"
echo ""
echo "To change settings:"
echo "  • Right-click on the icon → Settings"
echo "  • Or run: freetranscriber-setup"
echo ""
