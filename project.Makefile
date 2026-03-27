tests/model/%.py: tests/input/%.yaml
	$(RUN) gen-python $< > $@.tmp && mv $@.tmp $@

specification: src/docs/specification/compliance.md

docs/specification/compliance.md: tests/test_compliance/test_compliance_suite.py
	mkdir -p docs/specification
	$(RUN) pytest $< -s -q --tb no --disable-warnings > $@.tmp && perl -pne 's@^\.#@#@' $@.tmp > $@.tmp.md && pandoc -f gfm --toc --toc-depth=2 -s $@.tmp.md -o $@ && rm $@.tmp && rm $@.tmp.md

%-doctest: %
	$(RUN) python -m doctest --option ELLIPSIS --option NORMALIZE_WHITESPACE $<

doctest:
	$(RUN) python -m doctest --option ELLIPSIS --option NORMALIZE_WHITESPACE src/linkml_map/*.py src/linkml_map/*/*.py

# Transform a LinkML-Map TransformationSpecification to FAIR Mappings Schema
# This demonstrates mapping metadata elements from linkml-map to fair-mappings-schema
FAIR_EXAMPLE_DIR = tests/input/examples/fair_mappings_metadata
FAIR_OUTPUT_DIR = $(FAIR_EXAMPLE_DIR)/output

FAIR_LINKMLMAP_SPEC = $(FAIR_EXAMPLE_DIR)/transform/linkmlmap-to-fair.transformation.yaml
LINKML_SAMPLE_INPUT = $(FAIR_EXAMPLE_DIR)/data/sample-linkmlmap-spec.yaml
LINKMLMAP_SCHEMA = src/linkml_map/datamodel/transformer_model.yaml

$(FAIR_OUTPUT_DIR)/linkmlmap-fair-mappings.yaml: $(LINKML_SAMPLE_INPUT) $(FAIR_LINKMLMAP_SPEC)
	mkdir -p $(FAIR_OUTPUT_DIR)
	$(RUN) linkml-map map-data \
		-T $(FAIR_LINKMLMAP_SPEC) \
		-s $(LINKMLMAP_SCHEMA) \
		--source-type TransformationSpecification \
		--unrestricted-eval \
		$(LINKML_SAMPLE_INPUT) \
		-o $@

transform-to-fair: $(FAIR_OUTPUT_DIR)/linkmlmap-fair-mappings.yaml
	@echo "Transformed $(LINKML_SAMPLE_INPUT) to FAIR Mappings Schema format"
	@echo "Output: $(FAIR_OUTPUT_DIR)/linkmlmap-fair-mappings.yaml"
