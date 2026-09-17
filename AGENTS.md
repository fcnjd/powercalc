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
  written in English. This also applies to translatable source strings
  (`_()` msgids): the English text lives in the code, and translations
  (currently German) live in `powercalc/locale/` — see "Internationalization"
  below.
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

Optional packaged runtime under review:

- `Liblouis 3.39.0` — official Windows x64 DLL and German Grade 1 tables for
  reliable tactile-plot Braille labels. It is not a PyPI dependency: the
  Windows build downloads a SHA-256-pinned official archive. See
  `docs/spikes/liblouis-portability.md`.

Package/project manager:

- `uv`

## Current Structure

```text
powercalc/
	settings.py
	core/
		__init__.py
		calculator.py
		catalog.py
	gui/
		__init__.py
		app.py
		formatting.py
		index_dialog.py
		main_window.py
	i18n/
		__init__.py
	locale/
		powercalc.pot
		de/
			LC_MESSAGES/
				powercalc.po
				powercalc.mo
assets/
	powercalc.ico
	source/
		powercalc-icon.svg
installer/
	powercalc.iss
tests/
	test_core_calculator.py
	test_core_catalog.py
	test_gui_formatting.py
	test_gui_import.py
	test_gui_index_dialog.py
	test_i18n.py
	test_settings.py
tools/
	build.py
	check_version.py
	i18n.py
	release_notes.py
.github/
	workflows/
		ci.yml
		release.yml
babel.cfg
main.py
```

## Architecture Guidelines

- `core`: parsing, validation, evaluation, result objects, error objects
- `gui`: wxPython windows, controls, events, keyboard handling
- `i18n`: translation and localization
- `tests`: parser tests, calculation-core tests, error cases, and later
  GUI-adjacent logic

The GUI must access the calculation core only through clear public functions
and data types. The core must not depend on wxPython.

When the Liblouis spike is enabled, its narrow `ctypes` adapter lives in
`core/braille.py`; packaging and verified table extraction live in
`tools/liblouis.py`. Do not substitute a similarly named PyPI package for the
official runtime.

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
- menus are File, Edit, Options, and Help; Alt-key letters are reserved for
  menu access
- the Options menu uses native radio and check menu items for angle unit,
  decimal separator, number domain, logarithm mode, error sound, and
  language (System/English/Deutsch)
- changing the language saves immediately like other options, but only
  takes effect after restarting Powercalc (no live retranslation); unlike
  other options, this is confirmed with a modal dialog rather than a status
  bar message, since it is easy to miss and more consequential
- decimal precision is set through a small native dialog and is limited to
  1 through 100 significant digits
- option changes apply to the next calculation, save immediately, and do not
  rewrite the current input or output
- calculation errors play one system sound by default before the existing
  text error output receives focus; this can be disabled in Options
- `Ctrl+Shift+X` (also via Edit > Function Index...) opens a native
  searchable dialog listing every function and constant, sorted
  alphabetically by a descriptive display name (e.g. "Quadratwurzel von
  n"); each row shows the display name and the code it inserts as one
  line of text, e.g. "Quadratwurzel von n — sqrt(n)"
- keyboard focus starts on the list itself (not the search field), so a
  typed letter uses the native list type-ahead to jump straight to a
  matching row; Tab reaches a search field that filters the list live by
  case-insensitive substring match against both the display name and the
  raw function/constant name (e.g. typing "sqrt" finds "Quadratwurzel von
  n")
- Up/Down move the list selection whether focus is on the list or the
  search field; Enter or double-click on a row confirms and closes the
  dialog immediately; Escape cancels; OK is disabled when no rows match
- selecting an entry inserts its code at the current cursor position in
  the expression input; for functions, the first argument name is
  pre-selected so it can be typed over immediately (e.g. inserting `log`
  selects the `n` in `log(n, a)`); the argument separator matches the
  current decimal separator setting (`, ` in point mode, `; ` in comma
  mode); constants are inserted as plain text with the caret placed at
  the end; focus then returns to the expression input
- F1 opens a short Keyboard Commands help dialog
- the main window title includes the public version
- Help > About opens a concise native dialog with version information

GUI result formatting is deliberately presentation-only. It uses the core
`CalculationResult.decimal_text` but strips unnecessary trailing zeroes so
ordinary integer results such as `14.0000000000` are read as `14`.

Application settings are stored as readable versioned JSON. Installed and
development runs use the per-user configuration directory from `platformdirs`.
The portable ZIP alone contains `portable.json`; when this marker is beside
the executable, `settings.json` is stored there too. Invalid values fall back
field by field, while malformed files are backed up before defaults are
written. Persistence logic remains independent of wxPython.

## Current Core API Contract

The public calculation API currently lives in `powercalc.core`:

- `calculate(expression, options=None) -> CalculationOutcome`
- `EvaluationOptions`
- `CalculationOutcome`
- `CalculationResult`
- `CalculationError`
- `CalculationErrorCode`
- `FUNCTION_CATALOG` — a tuple of `CatalogEntry`, sorted alphabetically by
  `display_name`, describing every callable function and constant, used
  by the GUI's function/constant index dialog.
- `CatalogEntry(display_name, function_name, parameters)` — `parameters`
  holds the argument names shown to the user (e.g. `("n", "a")` for
  `log`); an empty tuple marks a constant, inserted as bare text.
  `FUNCTION_CATALOG` must stay in sync with `calculator.py`'s dispatch
  logic; `tests/test_core_catalog.py` enforces this with a round-trip
  `calculate()` check per entry.
- `build_insertion(entry, decimal_separator) -> (text, selection_start,
  selection_end)` — builds the text to insert for a catalog entry and the
  selection span of its first argument (empty span at the end of the text
  for constants), using the argument separator that matches
  `decimal_separator`.

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
- `EvaluationOptions.decimal_separator` accepts `"point"` (the default) or
  `"comma"`. It controls input parsing and the notation used by
  `CalculationResult.normalized_text`, `exact_text`, and `decimal_text`.
- `CalculationResult.input_text` always preserves the original input, while
  `CalculationResult.value` remains the canonical SymPy object. Use
  `str(result.value)` when raw canonical SymPy text is required.

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
- Point mode uses a decimal point and comma-separated function arguments.
  Semicolons are also accepted for arguments and normalize to commas.
- Comma mode uses a decimal comma and requires semicolons between function
  arguments, for example `log(8; 2)` and `min(1,5; 2,5)`.
- Separator normalization happens before the restricted AST parser. SymPy
  receives only canonical point notation; localized text is produced only
  after safe evaluation.

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

- All translatable, user-facing strings are wrapped in `_(...)`. `_` is
  installed globally into `builtins` by `powercalc.i18n` (Python
  stdlib `gettext`), not imported per module.
  `powercalc/__init__.py` installs an English passthrough translation as a
  side effect of the package import, so `_` always exists — including in
  tests and tools that import `powercalc.core`/`powercalc.gui` directly.
- `_()` msgids are English source strings, same as the rest of the code (see
  "Core Principles"). Do not scatter untranslated literals through GUI code
  or `core/catalog.py`; every user-facing string must go through `_()`.
- Keep translatable UI text separate from technical diagnostics:
  `CalculationError.message` (from `powercalc.core`) is intentionally still
  an untranslated English default for now; only the GUI-side prefix around
  it is translated (see `powercalc/gui/formatting.py`). Full error-message
  localization would require `calculator.py` to carry structured error
  parameters instead of pre-formatted strings, and is deliberately deferred.
- English and German are the shipped languages; German preserves the
  descriptive catalog wording used before this was introduced (e.g.
  "Quadratwurzel von n" for "Square root of n").
- Translation catalogs live in `powercalc/locale/<language>/LC_MESSAGES/
  powercalc.{po,mo}`; both `.po` and `.mo` are committed so the app runs
  directly from the source tree without a Babel build step. Regenerate them
  with `tools/i18n.py` (see "Tooling") after changing translatable strings.
- The startup language is resolved once, from `AppSettings.language`
  (`"system"`/`"en"`/`"de"`, default `"system"`) via
  `powercalc.i18n.resolve_startup_language`, which detects the Windows UI
  language for `"system"` and falls back to English. `main.py` resolves and
  installs the language *before* importing `powercalc.gui` (which
  transitively imports `powercalc.core.catalog`, evaluated once at import
  time) — this ordering is required, since `_()` calls at module level only
  observe whichever translation is installed when that module first loads.
- Changing the language in the GUI is restart-required, not live: this
  keeps `FUNCTION_CATALOG` a simple, eagerly-built module constant (no
  Core API change) instead of a function that must be rebuilt per language.
- `gui/app.py::run()` also sets a `wx.Locale` matching the resolved
  language, so native wx stock labels (e.g. dialog OK/Cancel) follow suit;
  `gettext` alone only covers Powercalc's own strings.
- `_` is not a normal Python builtin, so `pyproject.toml`'s
  `[tool.ruff] builtins = ["_"]` tells Ruff/pyflakes not to flag it as
  undefined.

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

Current development-only dependency:

- `babel` — extracts and compiles gettext catalogs via `tools/i18n.py`; not
  needed at runtime (the app only uses stdlib `gettext`)

Planned but not yet added:

- quality/testing: `pytest-cov`, `hypothesis`, `mypy`, `pre-commit`
- translation workflow: `polib` (only if a need beyond Babel appears)
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
uv run python -m tools.i18n extract
uv run python -m tools.i18n update
uv run python -m tools.i18n compile
```

Ruff conventions from `pyproject.toml`:

- line length: 80
- indentation: tabs
- line endings: LF
- `E501` enabled
- `W191` ignored because tabs are used

Keep this formatting when editing existing Python files.

## Versioning, Builds, and Releases

- The current version is `0.3.0-beta.1`.
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
