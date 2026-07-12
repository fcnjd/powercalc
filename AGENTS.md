# AGENTS.md

This file is the living working agreement for this repository. Keep it updated
whenever architecture, dependencies, tooling, workflow, or product direction
changes in a way that future contributors or agents need to know.

## Project Goal

`powercalc` is intended to become an accessible, professional desktop
calculator based on wxPython.

Development is intentionally incremental:

1. robust handling of ordinary typed mathematical expressions
2. functions such as `sin`, `cos`, `sqrt`, `log`, constants, and modes
3. history, copyable results, and clear errors
4. internationalization with `gettext` and, if useful, Babel
5. value tables and function evaluation
6. plotting and export, with tactile-graphics use cases in mind
7. equations, derivatives, and additional symbolic mathematics
8. build, check, and release automation, e.g. via GitHub Actions

## Core Principles

- Accessibility has priority over visual effects.
- Prefer native wxPython controls over custom-drawn widgets.
- Ensure full keyboard operability.
- Always make results, errors, and status available as text.
- Do not evaluate mathematical user input with Python `eval()`.
- Keep mathematical logic strictly separate from GUI code.
- Prefer small, testable modules.
- Add dependencies only when they serve a clear current purpose.
- Code, API names, error codes, internal messages, and docstrings must be
  written in English. User-visible localization will be added through the i18n
  layer later.
- Update this file when project structure, tooling, dependencies, architecture,
  or workflow decisions change.

## Current Technical State

Python version according to `pyproject.toml`:

- Python `>=3.13`

Current runtime dependencies:

- `wxPython` — native desktop GUI
- `sympy` — mathematical and symbolic engine
- `platformdirs` — platform-specific locations for settings, history, and
  later user data

Current development dependencies:

- `pyinstaller` — Windows desktop app bundling for release artifacts
- `ruff` — linting and formatting
- `pytest` — automated tests

Package/project manager:

- `uv`

## Current Structure

```text
powercalc/
	core/
		__init__.py
		calculator.py
	gui/
		__init__.py
		app.py
		formatting.py
		main_window.py
assets/
	powercalc.ico
	source/
		powercalc-icon.svg
installer/
	powercalc.iss
tests/
	test_core_calculator.py
	test_gui_formatting.py
	test_gui_import.py
tools/
	build.py
	check_version.py
	release_notes.py
.github/
	workflows/
		ci.yml
		release.yml
main.py
```

Expected later extensions:

```text
powercalc/
	i18n/
		...
```

## Architecture Guidelines

- `core`: parsing, validation, evaluation, result objects, error objects
- `gui`: wxPython windows, controls, events, keyboard handling
- `i18n`: translation and localization
- `tests`: parser tests, calculation-core tests, error cases, and later
  GUI-adjacent logic

The GUI must access the calculation core only through clear public functions
and data types. The core must not depend on wxPython.

## Current GUI Behavior

The first wxPython GUI increment is intentionally small and keyboard-first:

- native controls only: expression `wx.TextCtrl`, Calculate `wx.Button`,
  read-only result `wx.TextCtrl`, menu bar, and status bar
- initial focus starts in the expression input
- the result output must be reachable with Tab even before a calculation has
  moved focus there
- Enter in the expression input triggers calculation
- Calculate can also be reached by Tab and activated with Space or Enter
- successful calculations move focus to the result output and select all text
- errors are displayed in the result output as short text beginning with
  `Error:`
- `Ctrl+L` clears only the expression input, leaves the previous output
  unchanged, returns focus to input, and sets a short status message
- `Ctrl+C` copies the selected result/error text when focus is in the output
- menus are File, Edit, and Help; Alt-key letters are reserved for menu access
- F1 opens a short Keyboard Commands help dialog
- the main window title includes the public version
- Help > About opens a concise native dialog with version information

GUI result formatting is deliberately presentation-only. It uses the core
`CalculationResult.decimal_text` but strips unnecessary trailing zeroes so
ordinary integer results such as `14.0000000000` are read as `14`.

## Current Core API Contract

The public calculation API currently lives in `powercalc.core`:

- `calculate(expression, options=None) -> CalculationOutcome`
- `EvaluationOptions`
- `CalculationOutcome`
- `CalculationResult`
- `CalculationError`
- `CalculationErrorCode`

Important API rules:

- Use `CalculationOutcome.success(result)` and
  `CalculationOutcome.failure(error)` to construct outcomes.
- Do not directly instantiate `CalculationOutcome`; direct construction is
  intentionally unsupported to protect the `ok`/`result`/`error` invariants.
- `CalculationError.code` is a `CalculationErrorCode` enum member, not a raw
  string.
- `CalculationError.message` is an English default message for early UI use.
  Future localized UI should map from `CalculationErrorCode`.
- `CalculationResult.value` is intentionally public and may expose a SymPy
  expression for tests and future advanced features. GUI code should primarily
  use the text fields.
- Core API docstrings are the current source of API documentation until a
  dedicated user/developer documentation structure exists.

## Mathematics and Parser Rules

- Do not directly execute user input.
- Do not use SymPy string parsers such as `parse_expr` or string `sympify` for
  raw user input, because they rely on Python `eval()` internally.
- Validate user input first with the restricted safe AST parser, then translate
  it into SymPy objects.
- Explicitly define allowed functions and constants.
- Return understandable errors through `CalculationError`, not raw exceptions.
- Prefer result objects over plain strings for future extensibility.
- The core supports angle units `radian`, `degree`, and `gradian`.
  `radian` is the default. The angle unit applies only to trigonometric and
  inverse trigonometric functions.
- The default number domain is complex. Real-only mode is available through
  `EvaluationOptions`.
- The default `log` mode is calculator-style base 10. Natural-log mode is
  available through `EvaluationOptions`.

Examples of early target expressions:

- `2+3*4`
- `sin(pi/2)`
- `sqrt(2)`
- `log(10)`
- `(1+2)^3`
- `5!`

## Accessibility

When working on the GUI, always check:

- Is everything reachable by keyboard?
- Is the tab order logical?
- Do input, result, history, and buttons have meaningful labels?
- Are error messages available as text?
- Is the result copyable?
- Does the application work without a mouse?
- Are visual details also represented textually?

For later plotting features, always provide text/data alternatives in addition
to graphics:

- value table
- axis and range description
- textual summary
- exportable data

## Internationalization

- Keep code and internal strings English.
- Do not scatter final user-facing strings throughout the codebase.
- Use a translation-friendly boundary when GUI text is introduced.
- Keep translatable UI text separate from technical diagnostics.
- English and German are the likely first languages.
- Runtime localization should start with the Python standard-library
  `gettext`; optional workflow tools such as Babel or `polib` can be added when
  translation files are introduced.

## Dependency Rules

Do not add dependencies directly unless the user explicitly asks you to do so.
When a new dependency is needed, explain which command the user should run.

Runtime dependency:

```powershell
uv add <package>
```

Development dependency:

```powershell
uv add --dev <package>
```

Optional extras or dependency groups should be introduced only when the related
project phase is actually implemented.

Planned but not yet added:

- quality/testing: `pytest-cov`, `hypothesis`, `mypy`, `pre-commit`
- translation workflow: `Babel`, `polib`
- plotting/value tables: `numpy`, `matplotlib`
- export/tactile graphics: `svgwrite`, `Pillow`, `reportlab`
- advanced mathematics: `scipy`, possibly `lark`

`sympy` is sufficient for the current core. Introduce a dedicated parser
dependency such as `lark` only if the planned input language outgrows the safe
AST strategy.

## Tooling

Common `uv` commands:

```powershell
uv sync
uv run python main.py
uv run pytest
uv run ruff check .
uv run ruff format .
uv run ruff format --check .
uv run python -m tools.build portable
uv run python -m tools.build installer
uv run python -m tools.build all
```

Ruff conventions from `pyproject.toml`:

- line length: 80
- indentation: tabs
- line endings: LF
- `E501` enabled
- `W191` ignored because tabs are used

Keep this formatting when editing existing Python files.

## Versioning, Builds, and Releases

- The current version is `0.2.0-beta.1`.
- `pyproject.toml` `project.version` is the canonical project version.
- `powercalc.version.__version__` must match `pyproject.toml`; tests enforce
  this.
- Release tags use the format `v<version>`, for example
  `v0.2.0-beta.1`.
- Official packaged artifacts currently target Windows x64.
- PyInstaller builds a `onedir` app bundle.
- The portable ZIP and Inno Setup 7 installer are both produced from the same
  PyInstaller bundle.
- Inno Setup uses stable `AppId`
  `{655f06a0-68c6-4878-b32b-f102f3415ace}` so future installers upgrade the
  same application line instead of creating a separate product.
- The build helper prefers Inno Setup 7, including the per-user install path
  `%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe`.
- Beta builds are unsigned. README and release notes must keep the SmartScreen
  warning clear until code signing is introduced.
- Release artifacts include `SHA256SUMS.txt`.
- The editable icon source stays in `assets/source/`; only
  `assets/powercalc.ico` is used by packaged builds.
- Do not add Pillow for icon generation unless the icon-generation workflow is
  intentionally made a maintained project tool later.

## GitHub Actions

CI runs on push and pull request:

- `uv sync --frozen`
- Ruff check
- Ruff format check
- pytest
- GUI/package import smoke check

Release builds run when a `v*` tag is pushed:

- validate tag/version consistency
- run CI checks
- install Inno Setup 7
- build portable ZIP and installer
- generate checksums
- create a GitHub prerelease using notes from `CHANGELOG.md`

## Documentation Maintenance

Update this file when any of the following change:

- dependencies or optional extras
- project structure
- test, CI, or build process
- architecture decisions
- accessibility decisions
- parser or mathematics strategy
- public Core API contracts
- workflow rules for future agents or contributors
