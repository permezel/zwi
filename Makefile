#
# Makefile!
#
VERSION=$(shell grep __version__ src/zwi/__init__.py | head -1 | sed 's/.*= //' | sed "s/'//g")

all:
	@echo ${VERSION}

build: dist/zwi-${VERSION}.tar.gz

dist/zwi-${VERSION}.tar.gz:
	flit build

publish: build dist/.pub-zwi-${VERSION}

dist/.pub-zwi-${VERSION}:
	flit publish
	touch  dist/.pub-zwi-${VERSION}

devel: publish
	flit install -s

install: publish
	pip3 install --update zwi

