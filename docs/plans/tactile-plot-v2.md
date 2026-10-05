# Tactile function plot v2

Status: approved v2 plan, amended 2026-10-05 by the owner’s explicit
multiple-function request; implementation tracked by GitHub issue #4.

## Goal

Export up to six safely parsed, real-valued functions of `x` as a tactile graphic
from a native, keyboard-operable Powercalc dialog.

## Scope

- Multiple named functions on shared axes with a legend and profile-dependent
  tactile line/marker cycles.
- Separate `Swell paper` and `Embosser` content profiles.
- Separate SVG and high-resolution PNG output formats.
- A4 landscape default plus A4/A5 portrait/landscape sizes.
- Opt-in German Grade 1 Unicode Braille labels backed by the accepted bundled
  Liblouis runtime.

Not in scope: printer discovery/submission, vendor protocols, user-defined
line styles, or claims of universal printer/paper compatibility.

## Source-to-requirement matrix

| Source evidence | Requirement | UI / non-goal | Verification |
| --- | --- | --- | --- |
| Supplied notebook: `create_plot` and `add_plot` share axes, use a legend, and cycle line/marker styles. | Up to six independently parsed functions with optional legend names; monochrome styles distinguish curves by touch for either profile. | Add/remove function rows and legend labels; no custom style picker. | Multi-function export, legend/style and dialog tests. |
| Supplied notebook: `use_swell_paper_styles`, black line/marker styles. | Monochrome, high-contrast `Swell paper` encoding. | Profile choice; no custom-style picker. | Profile export test and UI check. |
| Notebook distinguishes swell-paper styling from other output. | `Embosser` is a separate content profile, not a device protocol. | Profile choice; no direct printing. | Profile export test. |
| Notebook: `use_braille`. | Explicit opt-in labels only through verified Liblouis translation. | `Braille labels` checkbox; disabled with explanation when runtime is missing. | Translator and export tests; Windows smoke test. |
| Owner requires a rendered alternative to avoid SVG viewer/font variance. | SVG and PNG are independently selectable. | Format choice controls save filter and suffix. | SVG/PNG type and dimension tests. |
| Owner chose selectable paper format with A4 landscape default. | Four physical paper-size choices. | Paper-size choice. | Figure-dimension and UI-default checks. |
| Existing calculator avoids `eval`. | Plot parser permits only `x` in addition to calculator syntax. | Function input and readable error. | Parser/security regression tests. |
| Native accessible UI rule. | All fields labelled and keyboard-reachable; only context-appropriate actions. | `Save plot…` and `Cancel`, no generic Apply/Yes/No. | Target-platform UI checklist. |

## UX contract

Dialog title: `Export tactile function plot`.

Tab order and defaults:

1. `Function of x` — current calculator input, otherwise `x^2`; optional
   `Function 1 legend label` defaults to the expression.
2. `Add function` inserts labelled expression and optional legend-label fields
   (up to six functions total), each with a `Remove function N` action.
3. `X minimum` — `-10`.
4. `X maximum` — `10`.
5. `Title` — `Tactile function plot`.
6. `Content profile` — `Swell paper` default; `Swell paper`, `Embosser`.
7. `Paper size` — `A4 landscape` default; A4/A5 portrait/landscape.
8. `File format` — `SVG` default; `SVG`, `PNG`.
9. `Braille labels` — unchecked; unavailable with an explanation when the
   Liblouis runtime cannot be loaded.
10. `Save plot…` opens a format-matched save dialog after validation.
    If a typed suffix changes to the selected format and the actual output
    file already exists, the actual filename receives an overwrite prompt.
11. `Cancel` closes without output.

Success appears in the status bar with exact filename and format. Validation
and export failures use readable text through the existing error path.

## Technical constraints

- wxPython stays in `gui`; parsing, profile data, dimensions, Braille boundary,
  and headless rendering stay in `core`.
- The profile determines tactile visual encoding, never file type.
- PNG uses fixed 300 DPI. SVG uses the same physical figure dimensions and
  emits text as paths so Braille does not rely on a viewer-installed font.
- Liblouis uses only the accepted official Windows runtime from the merged
  portability spike. No hand-written transcription is presented as Braille.
- Export writes a temporary sibling file and atomically replaces the requested
  path only after rendering succeeds.

## Acceptance criteria

1. Two or more named functions export on shared axes with a legend; each uses
   a different tactile style for either selectable monochrome profile.
2. Either profile exports SVG and PNG with matching suffix/filter/type;
   overwrite confirmation applies to the actual normalized output filename.
3. The four paper sizes are selectable, with A4 landscape default and tested
   physical dimensions.
4. Dialog labels, defaults, tab order and actions match this contract.
5. Invalid bounds, expressions, modes and unwritable paths are readable
   failures without a partial success claim.
6. Unsafe expressions remain rejected by the restricted parser.
7. Enabled Braille labels use the tested Liblouis runtime; otherwise the
   control is visibly unavailable.
8. Windows portable CI covers all required bundled runtime files and exports.
9. An independent reviewer checks this matrix, UI evidence, tests and CI before
   merge.
