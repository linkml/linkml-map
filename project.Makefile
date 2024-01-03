tests/model/%.py: tests/input/%.yaml
	$(RUN) gen-python $< > $@.tmp && mv $@.tmp $@

docs/specification/compliance.md: tests/test_compliance/test_compliance_suite.py
	mkdir -p docs/specification
	$(RUN) pytest $< -s -q --tb no --disable-warnings > $@.tmp && perl -pne 's@^\.#@#@' $@.tmp > $@ && rm $@.tmp

%-doctest: %
	$(RUN) python -m doctest --option ELLIPSIS --option NORMALIZE_WHITESPACE $<

doctest:
	$(RUN) python -m doctest --option ELLIPSIS --option NORMALIZE_WHITESPACE src/linkml_transformer/*.py src/linkml_transformer/*/*.py

