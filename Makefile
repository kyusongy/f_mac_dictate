VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
APP_NAME := f_mac_dictate
PLIST_SRC := com.f_mac_dictate.plist
PLIST_DEST := ~/Library/LaunchAgents/com.f_mac_dictate.plist
LABEL := com.f_mac_dictate

.PHONY: install run clean bundle launchagent unlaunchagent

install:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) main.py

clean:
	rm -rf build dist *.app

bundle: install
	$(PIP) install py2app
	$(PYTHON) setup.py py2app

launchagent:
	@# Stamp absolute paths into plist
	sed -e 's|__VENV_PYTHON__|$(CURDIR)/$(VENV)/bin/python|' \
	    -e 's|__MAIN_PY__|$(CURDIR)/main.py|' \
	    -e 's|__PROJECT_DIR__|$(CURDIR)|' \
	    $(PLIST_SRC) > $(PLIST_DEST)
	launchctl bootout gui/$$(id -u) $(PLIST_DEST) 2>/dev/null || true
	launchctl bootstrap gui/$$(id -u) $(PLIST_DEST)
	@echo "LaunchAgent installed and started."

unlaunchagent:
	launchctl bootout gui/$$(id -u) $(PLIST_DEST) 2>/dev/null || true
	rm -f $(PLIST_DEST)
	@echo "LaunchAgent removed."
