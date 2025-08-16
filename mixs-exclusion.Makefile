mixs.yaml:
	curl -L -o $@ https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/refs/heads/main/src/mixs/schema/mixs.yaml

biosample-schema.yaml: mixs.yaml mixs-exclusion-template.yaml
	uv run linkml-map derive-schema \
		-T $(word 2, $^) \
		-o $@ \
		$(word 1, $^)
