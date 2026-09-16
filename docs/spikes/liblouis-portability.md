# Liblouis portability spike

Status: implementation under review. Related: GitHub issue #2.

## Decision under test

Can Powercalc use Liblouis for reliable German Braille labels in its Windows
portable distribution without relying on an unofficial PyPI package?

## Chosen source and table

- Source: official Liblouis `3.39.0` Windows x64 release archive.
- Archive SHA-256:
  `64d669ac30f1411e0023b1cecc81c7a7b5374678ee41302c95ac8c7c8fbc6591`.
- Table: `de-g1.ctb`, German Grade 1 literary Braille, forward translation
  only. This is appropriate for plot labels; Powercalc does not offer
  back-translation.

The build downloads the pinned official archive, verifies its SHA-256, and
extracts `liblouis.dll` plus the table and every transitive `include` needed by
that table. No third-party package named `louis`, `Pylouis`, or similar is
used.

## Runtime boundary

`powercalc.core.braille.LiblouisBrailleTranslator` is a narrow `ctypes`
adapter. It loads only the bundled DLL, explicitly sets Liblouis' data path to
the bundled `share` directory in Liblouis' expected data layout, and selects
the documented table by name.
Missing DLLs, tables, or load failures become a readable unavailable state;
the future tactile-plot dialog must keep Braille labels disabled in that state.

## Evidence required for acceptance

1. Headless extraction tests prove checksum rejection and included-table
   closure.
2. The Windows GitHub Actions job builds the portable artifact.
3. The job imports the adapter against the bundled directory and verifies that
   German Grade 1 translates `abc` to `⠁⠃⠉`.
4. The later tactile-plot implementation separately proves that accepted
   translations are rendered reliably into SVG and PNG. This spike does not
   introduce a renderer or claim SVG/PNG output by itself.

## Decision rule

Adopt this runtime for tactile-plot Braille labels only if the Windows job and
the independent requirements review pass. Otherwise the future UI keeps
Braille labels unavailable; no handwritten transliteration is shipped as
correct Braille.
