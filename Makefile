MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
.SUFFIXES:
.SECONDARY:

RUN = uv run
SCHEMA_NAME = linkml_map
SOURCE_SCHEMA_PATH = src/linkml_map/datamodel/transformer_model.yaml
DOCDIR = docs

.PHONY: help status install test test-python update-packages gendoc testdoc serve deploy-gh-doc

help: status
	@echo ""
	@echo "make install -- install dependencies"
	@echo "make test -- runs tests"
	@echo "make gendoc -- regenerates the schema docs"
	@echo "make testdoc -- builds docs and runs local test server"
	@echo "make deploy-gh-doc -- publishes docs to GitHub Pages"
	@echo "make update-packages -- updates dependencies"
	@echo "make help -- show this help"
	@echo ""

status:
	@echo "Project: $(SCHEMA_NAME)"
	@echo "Source: $(SOURCE_SCHEMA_PATH)"

install:
	uv sync

# TODO: make this default
src/linkml_map/datamodel/transformer_model.py: src/linkml_map/datamodel/transformer_model.yaml
	# $(RUN) gen-pydantic --pydantic-version 2 $< > $@.tmp && mv $@.tmp $@
	$(RUN) gen-pydantic --template-dir templates/pydantic $< > $@.tmp && mv $@.tmp $@

test: test-python doctest
test-python:
	$(RUN) pytest

# N.b. this does not update pyproject.toml
# as of Apr 2025, uv does not have this feature
# see https://github.com/astral-sh/uv/issues/6794
update-packages:
	uv sync -U

# Test documentation locally
serve: mkd-serve

# Deploy gh docs
# https://github.com/linkml/linkml/issues/2193
#deploy-gh-doc: gendoc
deploy-gh-doc:
	$(RUN) mkdocs gh-deploy

gendoc:
	$(RUN) gen-doc -d $(DOCDIR)/schema $(SOURCE_SCHEMA_PATH) --index-name datamodel

testdoc: gendoc serve

MKDOCS = $(RUN) mkdocs
MKDOCS_ARGS =
mkd-%:
	$(MKDOCS) $* $(MKDOCS_ARGS)

include project.Makefile
