PYTHON=python3
VENV=.venv

.PHONY: venv install test lint pylint clean
 pylint: install
	$(VENV)/bin/pylint framework.py tests/
lint:
	@$(VENV)/bin/flake8 framework.py tests/

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(VENV)/bin/pip install -r requirements.txt

test:
	@$(VENV)/bin/pytest tests/ --maxfail=1 --disable-warnings -q

clean:
	rm -rf $(VENV)
