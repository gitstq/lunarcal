.PHONY: test zipapp wheel clean install

PY ?= python3

test:
	$(PY) -m unittest discover -s tests -v

zipapp:
	$(PY) scripts/build_zipapp.py

wheel:
	$(PY) -m pip install --upgrade build
	$(PY) -m build --wheel

install:
	$(PY) -m pip install .

clean:
	rm -rf build dist *.egg-info lunarcal.pyz
	find . -name __pycache__ -type d -exec rm -rf {} +
