#
# This is a helper makefile to run tox.
#

PYTHON3 ?= /usr/bin/python3.12
ACTIVATE ?= .venv/bin/activate
PIP ?= .venv/bin/pip
TOX ?= .venv/bin/tox

.PHONY: help
help:
	@echo "usage: make <target>"
	@echo ""
	@echo "targets:"
	@echo "  init       create python virtualenv to run tox"
	@echo "  format     reformat code with black"
	@echo "  lint       run lint checks"
	@echo "  test       run all tests"
	@echo "  build      build packages"
	@echo "  release    upload to pypi.org"
	@echo "  clean      remove generated files"
	@echo "  distclean  remove generated files and virtualenvs"

$(ACTIVATE):
	$(PYTHON3) -m venv .venv
	$(PIP) install -U pip setuptools
	$(PIP) install tox==4.12.0
	touch $(ACTIVATE)

.PHONY: init
init: $(ACTIVATE)

.PHONY: format
format: init
	$(TOX) -e format

.PHONY: lint
lint: init
	$(TOX) -e lint

.PHONY: test
test: lint
	$(TOX)

.PHONY: build
build: init
	$(TOX) -e build

.PHONY: release
release: init
	$(TOX) -e release

.PHONY: clean
clean:
	rm -f MANIFEST
	rm -rf */__pycache__/
	rm -rf *.egg-info/
	rm -rf build/
	rm -rf dist/

.PHONY: distclean
distclean: clean
	rm -rf .venv/
	rm -rf .tox/
