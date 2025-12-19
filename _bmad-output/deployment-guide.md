# Deployment Guide

FreeTranscriber is deployed as a standalone portable executable for Windows using **PyInstaller**.

## Build Requirements

- Python installed and added to PATH.
- All project dependencies installed (`pip install -r requirements.txt`).
- `pyinstaller` installed (`pip install pyinstaller`).

## Build Process

The project includes a build script `build_exe.bat` that automates the PyInstaller configuration.

1.  **Open Terminal** in the project root.
2.  **Run the Build Script**:
    ```cmd
    build_exe.bat
    ```

### Under the Hood
The script runs the following command:
```bash
pyinstaller --noconfirm --onefile --windowed --name "FreeTranscriber" ^
    --hidden-import=scipy.spatial.transform._rotation_groups ^
    --collect-all faster_whisper ^
    --collect-all PyQt6 ^
    src/main.py
```

- `--onefile`: Packages everything into a single `.exe`.
- `--windowed`: Suppresses the console window on launch.
- `--collect-all`: Ensures all data files for `faster_whisper` and `PyQt6` are included.

## Output

- The compiled executable will be placed in the `dist/` directory: `dist/FreeTranscriber.exe`.
- This file is **portable**: it can be copied to any Windows machine and run without installing Python or dependencies.
- **Note**: The first launch might be slow as it extracts embedded libraries to a temporary folder.

## Distribution

- Zip the `FreeTranscriber.exe` and distribute.
- **Updates**: Since it's a single file, updates are performed by replacing the `.exe` file.
