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
	@echo "installation:"
	@echo "  install        install package"
	@echo "  uninstall      uninstall package"
	@echo "  install-user   user mode install"
	@echo "  uninstall-user user mode uninstall"
	@echo "  install-dev    developer mode install"
	@echo "  uninstall-dev  developer mode uninstall"
	@echo "development:"
	@echo "  lint           run python linter"
	@echo "  test           run unit tests"
	@echo "  clean          delete generated files"
	@echo "  distclean      delete generated and config files"

Makefile.config: Makefile
	python configure.py >$@

include Makefile.config

version: $(NAME)/version.py
$(NAME)/version.py:
	echo "__version__ = u'$(VERSION)'" >$@

lint: version
	$(PYFLAKES) $(NAME)/*.py

test: version
	@echo todo

sdist: version
	$(PYTHON) setup.py sdist

wheel: version
	$(PYTHON) setup.py bdist_wheel

rpm: version
	$(PYTHON) setup.py bdist_rpm

deb: version
	$(PYTHON) setup.py --command-packages=stdeb.command bdist_deb

install: version
	$(MAKE) -f Makefile.$(INSTALL) $@

install-user: version
	$(MAKE) -f Makefile.$(INSTALL) $@

install-dev: version
	$(MAKE) -f Makefile.$(INSTALL) $@

uninstall:
	$(MAKE) -f Makefile.$(INSTALL) $@

uninstall-user:
	$(MAKE) -f Makefile.$(INSTALL) $@

uninstall-dev:
	$(MAKE) -f Makefile.$(INSTALL) $@

clean:
	rm -f *.pyc test/*.pyc $(NAME)/*.pyc
	rm -fr $(NAME).egg-info/ build/ dist/
	rm -fr $(NAME)*.tar.gz deb_dist/
	rm -f MANIFEST

distclean: clean
	rm -f $(NAME)/version.py
	rm -f Makefile.config
	rm -f files.txt
