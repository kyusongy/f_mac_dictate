from setuptools import setup

APP = ["main.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "LSUIElement": True,
    },
    "includes": [
        "config",
        "recorder",
        "transcriber",
        "output",
        "indicator",
        "hotkey",
    ],
    "packages": [
        "rumps",
        "pynput",
        "sounddevice",
        "numpy",
        "httpx",
        "dotenv",
        "objc",
        "AppKit",
        "Foundation",
        "Quartz",
        "CoreFoundation",
    ],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
