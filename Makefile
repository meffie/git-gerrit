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
	@echo "NAME=`python setup.py --name`"              >$@
	@echo "PIP=`which pip || echo missing`"            >>$@
	@echo "PYTHON=`which python || echo missing`"      >>$@
	@echo "PYFLAKES=`which pyflakes || echo missing`"  >>$@
	@if which pip >/dev/null; then \
		echo "MODE=pip" >>$@; \
	else \
		echo "MODE=setup" >>$@; \
	fi

include Makefile.config

init: $(NAME)/__init__.py

version.txt:
	(git describe --tags || echo 0.0.0) | sed -e 's/^v//' >$@

$(NAME)/__init__.py: __init__.py.in version.txt
	VERSION=`cat version.txt`; \
	sed -e "s/@VERSION@/'$${VERSION}'/" __init__.py.in >$@

lint: init
	$(PYFLAKES) $(NAME)/*.py

test: init
	@echo todo

sdist: init
	$(PYTHON) setup.py sdist

wheel: init
	$(PYTHON) setup.py bdist_wheel

rpm: init
	$(PYTHON) setup.py bdist_rpm

deb: init
	$(PYTHON) setup.py --command-packages=stdeb.command bdist_deb

install: init
	$(MAKE) -f Makefile.$(MODE) $@

install-user: init
	$(MAKE) -f Makefile.$(MODE) $@

install-dev: init
	$(MAKE) -f Makefile.$(MODE) $@

uninstall:
	$(MAKE) -f Makefile.$(MODE) $@

uninstall-user:
	$(MAKE) -f Makefile.$(MODE) $@

uninstall-dev:
	$(MAKE) -f Makefile.$(MODE) $@

clean:
	rm -f *.pyc test/*.pyc $(NAME)/*.pyc
	rm -fr $(NAME).egg-info/ build/ dist/
	rm -fr $(NAME)*.tar.gz deb_dist/
	rm -f MANIFEST
	rm -f version.txt
	rm -f $(NAME)/__init__.py

distclean: clean
	rm -f Makefile.config
	rm -f files.txt
