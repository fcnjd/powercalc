# Powercalc

Powercalc is an accessible desktop calculator built with wxPython. It is in
beta development and currently targets Windows x64 for packaged releases.

## Install or run

Powercalc beta releases are published on GitHub Releases as:

- a portable ZIP archive
- a Windows installer
- `SHA256SUMS.txt` for checksum verification

Portable use:

1. Download `Powercalc-<version>-windows-x64-portable.zip`.
2. Extract the archive.
3. Run `Powercalc.exe` from the extracted `Powercalc` folder.

Installer use:

1. Download `Powercalc-<version>-windows-x64-setup.exe`.
2. Run the installer.
3. Choose current-user or system-wide installation when prompted.

Beta builds are currently unsigned. Windows may show a SmartScreen warning.
Verify downloads with `SHA256SUMS.txt` when possible.

## Updates

Updates are manual for now. Download the newer ZIP or installer from GitHub
Releases. The installer uses a stable application identity so future installer
updates can replace an existing Powercalc installation cleanly.

## Development

Common commands:

```powershell
uv sync
uv run python main.py
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Build release artifacts locally:

```powershell
uv run python -m tools.build portable
uv run python -m tools.build installer
uv run python -m tools.build all
```

The installer target requires Inno Setup 7 on Windows. Set the `ISCC`
environment variable if `ISCC.exe` is not on `PATH`. The build helper also
checks the default per-user install path under
`%LOCALAPPDATA%\Programs\Inno Setup 7`.

## Icon assets

The editable source graphic is stored in `assets/source/`. The packaged app,
portable ZIP, and installer use only `assets/powercalc.ico`.
