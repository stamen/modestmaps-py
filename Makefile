VERSION=1.2.0
PACKAGE=ModestMaps-$(VERSION)
TARBALL=ModestMaps-Py-$(VERSION).tar.gz
DOCROOT=modestmaps.com:public_html/modestmaps

all: $(TARBALL)
	#

live: $(TARBALL)
	scp $(TARBALL) $(DOCROOT)/dist/
	python setup.py register

$(TARBALL):
	mkdir $(PACKAGE)
	ln setup.py $(PACKAGE)/

	mkdir $(PACKAGE)/ModestMaps
	ln ModestMaps/*.py $(PACKAGE)/ModestMaps/

	tar -czf $(TARBALL) $(PACKAGE)
	rm -rf $(PACKAGE)

clean:
	rm -rf $(TARBALL)
