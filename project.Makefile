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

