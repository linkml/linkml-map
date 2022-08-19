tests/model/%.py: tests/input/%.yaml
	$(RUN) gen-python $< > $@.tmp && mv $@.tmp $@
