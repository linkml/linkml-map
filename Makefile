MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
.SUFFIXES:
.SECONDARY:

RUN = uv run
# get values from about.yaml file
SCHEMA_NAME = $(shell sh ./utils/get-value.sh name)
SOURCE_SCHEMA_PATH = $(shell sh ./utils/get-value.sh source_schema_path)
SRC = src
DEST = project
PYMODEL = $(SRC)/$(SCHEMA_NAME)/datamodel
DOCDIR = docs

# basename of a YAML file in model/
.PHONY: all clean

help: status
	@echo ""
	@echo "make all -- makes site locally"
	@echo "make install -- install dependencies"
	@echo "make setup -- initial setup"
	@echo "make test -- runs tests"
	@echo "make testdoc -- builds docs and runs local test server"
	@echo "make deploy -- deploys site"
	@echo "make update-packages -- updates dependencies"
	@echo "make help -- show this help"
	@echo ""

status: check-config
	@echo "Project: $(SCHEMA_NAME)"
	@echo "Source: $(SOURCE_SCHEMA_PATH)"

setup: install gen-project gendoc git-init-add

install:
	uv sync
.PHONY: install

all: gen-project gendoc
%.yaml: gen-project
deploy: all deploy-gh-doc

# TODO: make this default
src/linkml_map/datamodel/transformer_model.py: src/linkml_map/datamodel/transformer_model.yaml
	$(RUN) gen-pydantic --pydantic-version 2 $< > $@.tmp && mv $@.tmp $@

# generates all project files
# TODO: combine pydantic into this step
gen-project: $(PYMODEL) src/linkml_map/datamodel/transformer_model.py
	$(RUN) gen-project -X sqltable -d $(DEST) $(SOURCE_SCHEMA_PATH)

test: test-python doctest
test-python:
	$(RUN) pytest
test-project:
	$(RUN) gen-project -d tmp $(SOURCE_SCHEMA_PATH)

check-config:
	@(grep my-datamodel about.yaml > /dev/null && printf "\n**Project not configured**:\n\n  - Remember to edit 'about.yaml'\n\n" || exit 0)

convert-examples-to-%:
	$(patsubst %, $(RUN) linkml-convert  % -s $(SOURCE_SCHEMA_PATH) -C Person, $(shell find src/data/examples -name "*.yaml"))

examples/%.yaml: src/data/examples/%.yaml
	$(RUN) linkml-convert -s $(SOURCE_SCHEMA_PATH) -C Person $< -o $@
examples/%.json: src/data/examples/%.yaml
	$(RUN) linkml-convert -s $(SOURCE_SCHEMA_PATH) -C Person $< -o $@
examples/%.ttl: src/data/examples/%.yaml
	$(RUN) linkml-convert -P EXAMPLE=http://example.org/ -s $(SOURCE_SCHEMA_PATH) -C Person $< -o $@

# N.b. this does not update pyproject.toml
# as of Apr 2025, uv does not have this feature
# see https://github.com/astral-sh/uv/issues/6794
update-packages:
	uv sync -U

# Test documentation locally
serve: mkd-serve

deploy: mkd-deploy

# Deploy gh docs
# https://github.com/linkml/linkml/issues/2193
#deploy-gh-doc: gendoc
deploy-gh-doc:
	$(RUN) mkdocs gh-deploy



# Python datamodel
$(PYMODEL):
	mkdir -p $@

# docs directory
$(DOCDIR):
	mkdir -p $@

gendoc: $(DOCDIR)
	$(RUN) gen-doc -d $(DOCDIR)/schema $(SOURCE_SCHEMA_PATH) --index-name datamodel

testdoc: gendoc serve

MKDOCS = $(RUN) mkdocs
mkd-%:
	$(MKDOCS) $* $(MKDOCS_ARGS)

PROJECT_FOLDERS = sqlschema shex shacl protobuf prefixmap owl jsonschema jsonld graphql excel
git-init-add: git-init git-add git-commit git-status
git-init:
	git init
git-add:
	git add .gitignore .github Makefile LICENSE *.md examples utils about.yaml mkdocs.yml uv.lock project.Makefile pyproject.toml src/linkml/*yaml src/*/datamodel/*py src/data
	git add $(patsubst %, project/%, $(PROJECT_FOLDERS))
git-commit:
	git commit -m 'Initial commit' -a
git-status:
	git status

clean:
	rm -rf $(DEST)
	rm -rf tmp

include project.Makefile
