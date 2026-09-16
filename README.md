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

The portable archive keeps `settings.json` beside `Powercalc.exe`. The
included `portable.json` file identifies this storage mode and should not be
deleted. Installer and development runs store settings in the current
Windows user's application configuration folder.

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

## Calculation options

Press `Alt+O` to open the Options menu. It provides native keyboard-accessible
radio and check items for angle unit, decimal separator, number domain,
logarithm mode, decimal precision, and the optional calculation error sound.
Changes apply to the next calculation and are saved immediately.

Point mode uses commas between function arguments. Comma mode uses decimal
commas and semicolons between function arguments, for example `log(8; 2)`.

## Tactile function plots

Use **File > Export Tactile Plot** (`Ctrl+Shift+P`) to export a real-valued
function of `x` as SVG. The exporter uses the same restricted parser as the
calculator, so only the calculator's allowed functions and the one variable
`x` are accepted. The SVG has thick black lines, periodic markers, prominent
axes, and a dotted reference grid for transfer to swell paper or embossers.
The optional Braille-label setting uses a deliberately limited uncontracted
mapping; review labels before production embossing.

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
