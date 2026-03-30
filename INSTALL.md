# INSTALL.md — Fusion 360 → Roland GX-24 Vinyl Cutter (HPGL)

This project adds two Fusion 360 commands:
- **GX-24: Export HPGL** (creates a `.plt` / HPGL file)
- **GX-24: Export + Send** (tries to launch the helper to send to the cutter)

✅ Recommended workflow: **Export HPGL in Fusion → run the helper shortcut**  
This avoids occasional Fusion quirks around launching external scripts.

---

## 0) What you need (checklist)

- Windows 10/11 laptop/PC
- Autodesk Fusion 360 installed
- Roland GX-24 connected by USB
- GX-24 Windows driver installed (so it shows up as a printer)
- Python installed (for the helper)
- pywin32 installed (for printer RAW sending)

---

## 1) Install the Roland GX-24 driver (Windows)

**Goal:** The cutter should appear in Windows as a printer named something like **“Roland GX-24”**.

1. Go to the Roland driver/support page:
   - Roland DGA GX-24 support page: https://www.rolanddga.com/support/products/cutting/camm-1-gx-24-24-vinyl-cutter?
   - Roland DG Download Center GX-24 page: https://downloadcenter.rolanddg.com/GX-24?  

2. Download the **CAMM-1 driver** for your Windows version (Windows 10/11 is typical).

3. Unzip the download (if it’s zipped), then run **SETUP.exe**.

4. Plug in the GX-24 via USB (if it isn’t already), and wait for Windows to finish detecting it.

5. Confirm it installed:
   - Open **Settings → Bluetooth & devices → Printers & scanners**
   - You should see **Roland GX-24** listed.

If you do NOT see it, please re-attempt the install — the driver install is required for sending cuts.

---

## 2) Install the Fusion 360 Add-in

Autodesk’s official “install add-in” guide is here: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-install-an-ADD-IN-and-Script-in-Fusion-360.html?

### 2.1 Download this repo
Option A (easiest): Download the repo ZIP from GitHub and unzip it.  
Option B: Clone it with Git if you know how.

### 2.2 Copy the add-in folder into Fusion’s AddIns folder

1. Press **Win + R**
2. Paste this and press Enter:

%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns

3. Copy the **entire** add-in folder into that directory.

The folder you copy should contain:
- `RolandGX24Addin.py`
- `RolandGX24Addin.manifest`
- a `helper` folder (with the sender script)

### 2.3 Enable the add-in in Fusion
1. Open Fusion 360
2. Go to **UTILITIES → Add-Ins**
3. On the **Add-Ins** tab, find the add-in (name may reference GX-24 / Roland)
4. Click **Run**
5. (Recommended) Check **Run on Startup**

You should now see two commands:
- **GX-24: Export HPGL**
- **GX-24: Export + Send**

If you don’t see them, restart Fusion after running the add-in once.

---

## 3) Install Python (needed for the helper)

**Goal:** You can run the sender helper script.

1. Download Python for Windows from the official site:
- Python Windows downloads: https://www.python.org/downloads/windows/?

2. Run the installer.
- IMPORTANT: Check **“Add Python to PATH”** during install (if shown).
- Use the default install options unless otherwise needed.

3. Verify Python works:
- Open **PowerShell** (Start Menu → type “PowerShell”)
- Run:
  ```
  python --version
  ```
You should see a version like Python 3.x.x.

If `python` is not recognized, try:

py --version


---

## 4) Install pywin32 (needed to send HPGL to the cutter)

The helper uses **pywin32** to send a RAW print job to the GX-24 printer.  
pywin32 official package info: https://pypi.org/project/pywin32/?

1. Open **PowerShell**
2. Run:

python -m pip install --upgrade pip
python -m pip install --upgrade pywin32


If `python` doesn’t work but `py` does, use:

py -m pip install --upgrade pip
py -m pip install --upgrade pywin32


---

## 5) Create a clickable shortcut for the Helper (recommended)

**Why:** Fusion sometimes blocks or fails to launch external helpers.  
A shortcut is reliable and easy.

### 5.1 Find pythonw.exe
pythonw.exe runs Python without opening a console window.

Typical path:
- `C:\Users\<yourname>\AppData\Local\Programs\Python\Python3xx\pythonw.exe`

If you’re unsure, you can search:
- Start Menu → type `pythonw.exe`

### 5.2 Create a Desktop shortcut
1. Right-click Desktop → **New → Shortcut**
2. For the “location”, use:

C:\Path\To\pythonw.exe "C:\Path\To\Fusion AddIn\helper\send_to_printer.py"

Example (you must adjust paths to your machine):

C:\Users\tyler\AppData\Local\Programs\Python\Python310\pythonw.exe "C:\Users\tyler\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\Fusion360-RolandGX24-Addin\helper\send_to_printer.py"


3. Name it: `GX-24 Sender`

Now you can double-click `GX-24 Sender` any time to send a `.plt` file.

---

## 6) How to use (full workflow)

### 6.1 Export from Fusion
1. In Fusion 360, open your design
2. Make sure your cut geometry is in a **2D sketch**
3. Run **GX-24: Export HPGL**
4. Select your sketch curves
5. Set options:
   - Units: mm or inch
   - Scale Factor: usually 1.0
   - Tolerance: start with 0.1 mm
   - Origin: choose bottom left corner, most commonly
   - Output path: use Downloads (recommended)
   - Filename: e.g. `output.plt`
6. Click OK to export

### 6.2 Send to the cutter
1. Double-click **GX-24 Sender**
2. Choose your `.plt` file
3. Choose printer: **Roland GX-24**
4. Click **Send**

---

## 7) Troubleshooting

### “I don’t see Roland GX-24 in printers”
- Reinstall the GX-24 driver (Section 1).
- Check USB cable / port.

### “The helper won’t run / says win32print missing”
- Install pywin32 again (Section 4).
- Make sure you’re running the helper with the same Python that you installed pywin32 into.

### “It cuts mirrored / upside down”
- Use the add-in’s origin settings as instructed.
- If the cutter treats origin differently, double check the vinyl cutter setup

### “Fusion asks me to save the design”
- Use the recommended workflow: Export HPGL → run the helper shortcut.
- Saving your Fusion file also resolves some Fusion API restrictions.
