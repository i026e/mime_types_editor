export SHELL = sh

PACKAGE = mime-editor-gui

all:

pot:
	mkdir -p ./po
	find . -iname "*.py" | xargs xgettext --default-domain="$(PACKAGE)" --sort-output --output="./po/$(PACKAGE).pot"
	find . -iname "*.glade" | xargs xgettext --join-existing --sort-output -L Glade -k_ -kN_ --keyword=translatable --output="./po/$(PACKAGE).pot"

	sed -i 's/CHARSET/UTF-8/' po/$(PACKAGE).pot
	sed -i 's/PACKAGE VERSION/$(PACKAGE) $(VERSION)/' po/$(PACKAGE).pot
	sed -i 's/PACKAGE/$(PACKAGE)/' po/$(PACKAGE).pot

update-po: pot
	for i in po/*.po ;\
	do \
	mv $$i $${i}.old ; \
	(msgmerge $${i}.old po/$(PACKAGE).pot | msgattrib --no-obsolete > $$i) ; \
	rm $${i}.old ; \
	done

translations: ./po/*.po
	mkdir -p locale
	@for po in $^; do \
		language=`basename $$po`; \
		language=$${language%%.po}; \
		target="locale/$$language/LC_MESSAGES"; \
		mkdir -p $$target; \
		msgfmt --output=$$target/$(PACKAGE).mo $$po; \
	done
