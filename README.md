# AutoClicker
Autoclicker made with AI because i dont trust sketchy websites
---

## Features

- **Adjustable CPS** up to 500 clicks/second (your mouse's cardio, not yours)
- **Left / Right / Middle click** support — we don't discriminate
- **Click at current cursor position** or lock it to a **fixed spot** on screen
- **Key Presser** — type any key (`a`, `5`, `space`, `enter`, `f1`, `up`, etc.) and have it auto-pressed
  - **Repeated mode** — press/release at a set rate
  - **Continuous mode** — just holds the key down, no questions asked
- **Click / press limits** so it stops itself instead of running forever like your browser tabs
- **Global hotkeys** — F6 and F7 work even if the window isn't focused, F9 is the "oh no" emergency stop
- Dark, edgy UI with a colorblind-safe status system (icon + text + color — nobody's left guessing what "green" means)

## Requirements

- Windows (packaged build), or Python 3.9+ if running the script directly
- If running from source: `pip install pynput`

## Running it

**If you built the `.exe`** (see `BUILD_INSTRUCTIONS.md`): just double-click it. That's the whole manual.

**If running the Python script directly:**
```
python autoclicker.py
```

## Controls

| Key    | Does what |
|--------|-----------|
| **F6** | Start/stop the mouse clicker |
| **F7** | Start/stop the key presser |
| **F9** | Emergency stop — kills both, no mercy |

## A quick, honest word on 500 CPS

Sending 500 clicks a second is easy. Whether the app you're clicking into actually *registers* all 500 is between you, the operating system, and whatever input-polling decisions that app made. This tool doesn't cheat physics — it just clicks really, really fast and lets the target app sort out its own feelings about that.

## Building your own `.exe`

Full steps are in `BUILD_INSTRUCTIONS.md`. Short version: `pip install pyinstaller`, then `pyinstaller autoclicker.spec`, then go touch grass while it builds.

## Disclaimer

Auto clickers can violate the terms of service of some games and applications that's on the app you're using it in, not this README. Use responsibly, don't get banned, and don't blame the icon.

i dont fucking care if you actually get banned, im also not responsible xd.
