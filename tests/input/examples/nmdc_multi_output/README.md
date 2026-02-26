# NMDC Multi-Output Demo Fixture

This fixture models a tiny NMDC-style biosample transformation for CLI multi-output testing.

Command exercised by tests:

```bash
linkml-map map-data \
  -T tests/input/examples/nmdc_multi_output/transform/nmdc_biosample.transform.yaml \
  -s tests/input/examples/nmdc_multi_output/source/nmdc_biosample_source.yaml \
  --source-type BiosampleRaw \
  --unrestricted-eval \
  -f jsonl \
  -o out.jsonl \
  -O out.tsv \
  -O out.json \
  tests/input/examples/nmdc_multi_output/data/BiosampleRaw.tsv
```

The transform preserves key biosample fields and parses `depth` values like `"12.5 m"` into `depth_value` and `depth_unit`.
It also derives `collection_year` from `collection_date` and handles malformed/empty depth values by emitting nulls.
