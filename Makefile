# Copyright (c) 2018 Sine Nomine Associates
#
# Helper makefile to package, locally install, and
# perform development tasks.
#

help:
	@echo "usage: make <target> [<target> ...]"
	@echo "packaging:"
	@echo "  sdist          create source distribution"
	@echo "  wheel          create wheel distribution"
	@echo "  rpm            create rpm package"
	@echo "  deb            create deb package"
	@echo "  upload         upload to packages to pypi.org"
	@echo "installation:"
	@echo "  install        install package"
	@echo "  uninstall      uninstall package"
	@echo "  install-user   user mode install"
	@echo "  uninstall-user user mode uninstall"
	@echo "  install-dev    developer mode install"
	@echo "  uninstall-dev  developer mode uninstall"
	@echo "development:"
	@echo "  lint           run python linter"
	@echo "  readme         generate the readme file"
	@echo "  scripts        generate the wrapper scripts"
	@echo "  checkdocs      check syntax of documentation files"
	@echo "  test           run unit tests"
	@echo "  clean          delete generated files"
	@echo "  distclean      delete generated and config files"

Makefile.config: configure.py
	python configure.py >$@

include Makefile.config

$(NAME)/_version.py:
	echo "__version__ = u'$(VERSION)'" >$@

README.rst: README.rst.in
	$(PYTHON) genreadme.py >README.rst

.PHONY: generated
generated: Makefile.config $(NAME)/_version.py README.rst

.PHONY: lint
lint: generated
	$(PYFLAKES) $(NAME)/*.py

.PHONY: readme
readme:
	$(PYTHON) genreadme.py >README.rst

.PHONY: scripts
scripts:
	$(PYTHON) genscripts.py

# requires collective.checkdocs
.PHONY: checkdocs
checkdocs:
	$(PYTHON) setup.py checkdocs

.PHONY: test
test: generated
	@echo todo

.PHONY: sdist
sdist: generated
	$(PYTHON) setup.py sdist

.PHONY: wheel
wheel: generated
	$(PYTHON) setup.py bdist_wheel

.PHONY: rpm
rpm: generated
	$(PYTHON) setup.py bdist_rpm

.PHONY: deb
deb: generated
	$(PYTHON) setup.py --command-packages=stdeb.command bdist_deb

.PHONY: upload
upload: sdist wheel
	twine upload dist/*

.PHONY: install
install: generated
	$(MAKE) -f Makefile.$(INSTALL) $@

.PHONY: install-user
install-user: generated
	$(MAKE) -f Makefile.$(INSTALL) $@

.PHONY: install-dev
install-dev: generated
	$(MAKE) -f Makefile.$(INSTALL) $@

.PHONY: uninstall
uninstall:
	$(MAKE) -f Makefile.$(INSTALL) $@

.PHONY: uninstall-user
uninstall-user:
	$(MAKE) -f Makefile.$(INSTALL) $@

.PHONY: uninstall-dev
uninstall-dev:
	$(MAKE) -f Makefile.$(INSTALL) $@

.PHONY: clean
clean:
	rm -f *.pyc test/*.pyc $(NAME)/*.pyc
	rm -fr $(NAME).egg-info/ build/ dist/
	rm -fr $(NAME)*.tar.gz deb_dist/
	rm -f MANIFEST

.PHONY: distclean
distclean: clean
	rm -f $(NAME)/_version.py
	rm -f Makefile.config
	rm -f files.txt
