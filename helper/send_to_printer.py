"""Small helper UI to send a HPGL file directly to a Windows printer as RAW data."""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import importlib.util
from typing import Optional
win32print = importlib.util.find_spec('win32print')
if win32print:
    import win32print


class PrinterApp:
    def __init__(self, root: tk.Tk, initial_file: Optional[str] = None):
        self.root = root
        self.root.title('Roland GX-24 Sender')
        self.file_var = tk.StringVar(value=initial_file or '')
        self.printer_var = tk.StringVar()

        self._build_ui()
        self._load_printers()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=12)
        frame.grid(sticky='nsew')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        ttk.Label(frame, text='HPGL File (.plt)').grid(row=0, column=0, sticky='w')
        ttk.Entry(frame, textvariable=self.file_var, width=52).grid(row=1, column=0, sticky='ew', padx=(0, 8))
        ttk.Button(frame, text='Browse…', command=self._browse).grid(row=1, column=1, sticky='ew')

        ttk.Label(frame, text='Printer').grid(row=2, column=0, sticky='w', pady=(12, 0))
        self.printer_combo = ttk.Combobox(frame, textvariable=self.printer_var, state='readonly', width=50)
        self.printer_combo.grid(row=3, column=0, columnspan=2, sticky='ew')

        ttk.Button(frame, text='Send to Printer', command=self._send).grid(row=4, column=0, columnspan=2, sticky='ew', pady=(12, 0))
        frame.columnconfigure(0, weight=1)

    def _browse(self):
        path = filedialog.askopenfilename(filetypes=[('HPGL files', '*.plt'), ('All files', '*.*')])
        if path:
            self.file_var.set(path)

    def _load_printers(self):
        if not win32print:
            messagebox.showerror('Missing dependency', 'pywin32 is not installed. Install it with: pip install pywin32')
            return

        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        printers = [p[2] for p in win32print.EnumPrinters(flags)]
        self.printer_combo['values'] = printers

        default = win32print.GetDefaultPrinter()
        if default in printers:
            self.printer_var.set(default)
        elif printers:
            self.printer_var.set(printers[0])

    def _send(self):
        if not win32print:
            return

        file_path = self.file_var.get().strip()
        printer_name = self.printer_var.get().strip()

        if not file_path or not os.path.isfile(file_path):
            messagebox.showerror('Invalid file', 'Select a valid .plt file.')
            return

        if not printer_name:
            messagebox.showerror('No printer', 'Select a printer first.')
            return

        try:
            with open(file_path, 'rb') as f:
                payload = f.read()

            handle = win32print.OpenPrinter(printer_name)
            try:
                job = win32print.StartDocPrinter(handle, 1, ('Fusion360 HPGL', None, 'RAW'))
                try:
                    win32print.StartPagePrinter(handle)
                    win32print.WritePrinter(handle, payload)
                    win32print.EndPagePrinter(handle)
                finally:
                    win32print.EndDocPrinter(handle)
            finally:
                win32print.ClosePrinter(handle)

            messagebox.showinfo('Success', f'Sent {len(payload)} bytes to {printer_name}.')
        except Exception as ex:
            messagebox.showerror('Print error', str(ex))


def main():
    initial_file = sys.argv[1] if len(sys.argv) > 1 else None
    root = tk.Tk()
    PrinterApp(root, initial_file)
    root.mainloop()


if __name__ == '__main__':
    main()
