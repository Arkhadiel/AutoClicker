# Building AutoClicker.exe

I've set everything up so this looks and behaves like a real installed app
instead of a Python script: custom icon, no console window, and proper
Windows file metadata (shows "AutoClicker" and version info when you
right-click > Properties).

**One important limitation:** I can't generate the actual `.exe` for you
from here — PyInstaller has to run on the same OS you're targeting, and I'm
working in a Linux environment. You'll need to run one command on your own
Windows machine, which takes about a minute. Here's exactly how:

## Files you need (all in this download)
- `autoclicker.py` — the app itself
- `icon.ico` — the app icon
- `autoclicker.spec` — tells PyInstaller how to package it
- `version_info.txt` — Windows file properties (name, version, copyright)

Put all four files in the **same folder**.

## Steps (on Windows, in that folder)

```
pip install pyinstaller pynput
pyinstaller autoclicker.spec
```

That's it. PyInstaller will create a `dist` folder containing:

```
dist\AutoClicker.exe
```

That single `.exe` is fully standalone — no Python install needed to run it,
no console window popping up, has your custom icon, and shows proper
version/company info in its file Properties. That's the file you can post
or share.

## Notes
- First run may take a second or two longer than a plain script, since
  PyInstaller unpacks itself into a temp folder — that's normal for
  single-file executables.
- Some antivirus/SmartScreen tools flag unsigned PyInstaller executables
  from unknown publishers (this is common for any small unsigned app, not
  specific to this one). If you plan to distribute it widely, code-signing
  a certificate is the fix, but that costs money and is usually overkill
  for sharing something with friends or a small community.
- If you ever edit `autoclicker.py`, just rerun `pyinstaller autoclicker.spec`
  to rebuild.
