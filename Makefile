VERSION:=$(shell cat VERSION)
PACKAGE=ModestMaps-$(VERSION)
TARBALL=$(PACKAGE).tar.gz
DOCROOT=py.modestmaps.com:/var/www/py.modestmaps.com

all: $(TARBALL)
	#

live: $(TARBALL)
	scp $(TARBALL) $(DOCROOT)/dist/
	python setup.py register

$(TARBALL):
	mkdir $(PACKAGE)
	ln setup.py $(PACKAGE)/
	ln VERSION $(PACKAGE)/

	mkdir $(PACKAGE)/ModestMaps
	ln ModestMaps/*.py $(PACKAGE)/ModestMaps/

	rm $(PACKAGE)/ModestMaps/__init__.py
	cp ModestMaps/__init__.py $(PACKAGE)/ModestMaps/__init__.py
	perl -pi -e 's#\bN\.N\.N\b#$(VERSION)#' $(PACKAGE)/ModestMaps/__init__.py

	tar -czf $(TARBALL) $(PACKAGE)
	rm -rf $(PACKAGE)

clean:
	rm -rf $(TARBALL)
