# Fusion 360 Roland GX-24 Add-In

This add-in creates two Fusion 360 commands:

1. **GX-24: Export HPGL** — exports selected sketch curves into an HPGL (`.plt`) file.
2. **GX-24: Export + Send** — exports and then launches a small Python helper UI to send the HPGL file to a printer using `win32print` RAW output.

## Command inputs

- **Sketch Curves**: select one or more sketch curves (2D).
- **Units**: `mm` or `inch`.
- **Scale Factor**: multiplicative scale on output coordinates.
- **Tolerance**: sampling tolerance used for arcs/curves.
- **Origin**:
  - Lower Left of Bounding Box
  - Sketch Origin
- **Output Path**
- **Filename** (`.plt` auto-appended if omitted)

> Notes:
> - Y output is flipped for GX-24 style top-left plotter coordinates so the cut origin aligns to the lower-left of exported geometry.
> - Output Path defaults to your user `Downloads` folder (or home folder fallback).

## Install

Full installation instructions noted in INSTALL.md.

1. Put this folder in your Fusion 360 AddIns directory.
2. In Fusion 360, go to **Scripts and Add-Ins** and run **RolandGX24Addin**.

## Helper dependencies (Windows)

The sender helper requires pywin32:

```bash
pip install pywin32
```

Then choose your printer and send the generated `.plt` file as a RAW print job.

## Credit
Created by Tyler Widener, assisted by ChatGPT and Codex.