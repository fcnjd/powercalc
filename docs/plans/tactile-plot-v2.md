# Tactile function plot v2

Status: approved plan; implementation tracked by GitHub issue #4.

## Goal

Export one safely parsed, real-valued function of `x` as a tactile graphic
from a native, keyboard-operable Powercalc dialog.

## Scope

- Separate `Swell paper` and `Embosser` content profiles.
- Separate SVG and high-resolution PNG output formats.
- A4 landscape default plus A4/A5 portrait/landscape sizes.
- Opt-in German Grade 1 Unicode Braille labels backed by the accepted bundled
  Liblouis runtime.

Not in scope: printer discovery/submission, vendor protocols, multiple series,
legends, user-defined line styles, or claims of universal printer/paper
compatibility.

## Source-to-requirement matrix

| Source evidence | Requirement | UI / non-goal | Verification |
| --- | --- | --- | --- |
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

1. `Function of x` — current calculator input, otherwise `x^2`.
2. `X minimum` — `-10`.
3. `X maximum` — `10`.
4. `Title` — `Tactile function plot`.
5. `Content profile` — `Swell paper` default; `Swell paper`, `Embosser`.
6. `Paper size` — `A4 landscape` default; A4/A5 portrait/landscape.
7. `File format` — `SVG` default; `SVG`, `PNG`.
8. `Braille labels` — unchecked; unavailable with an explanation when the
   Liblouis runtime cannot be loaded.
9. `Save plot…` opens a format-matched save dialog after validation.
10. `Cancel` closes without output.

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

1. Both profiles are selectable, monochrome, and intentionally distinct.
2. Either profile exports SVG and PNG with matching suffix/filter/type.
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
