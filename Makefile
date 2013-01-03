PREFIX := /usr

install:
	mkdir -p $(DESTDIR)$(PREFIX)/{bin,share/{applications,qtarot,icons}}
	install -Dm644 *.py $(DESTDIR)$(PREFIX)/share/qtarot
	install -Dm644 QTarot.desktop $(DESTDIR)$(PREFIX)/share/applications
	install -Dm755 qtarot.sh $(DESTDIR)$(PREFIX)/bin/qtarot
	cp -R decks $(DESTDIR)$(PREFIX)/share/qtarot
	cp -R deck_defs $(DESTDIR)$(PREFIX)/share/qtarot
	cp -R layouts $(DESTDIR)$(PREFIX)/share/qtarot
	cp -R hicolor $(DESTDIR)$(PREFIX)/share/icons
	install -Dm644 *.{xsd,html} $(DESTDIR)$(PREFIX)/share/qtarot
