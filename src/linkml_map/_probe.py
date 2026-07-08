"""Debug harness for the ff846709 sparse-empty regression (linkml-map #284).

Gated by LINKML_MAP_PROBE=1. Logs ONLY counts, column/table names, and value *types* —
never cell values — so it is safe to run against protected data and read the logs.

Also honors LINKML_MAP_NO_COERCE=1 (handled in data_loaders.DataLoader._schema_loader_kwargs):
the isolation test — reverts *only* the schema_path/target_class forwarding of ff846709.

Localizes where rows vanish across the three stages, per class_derivation:
  loader rows (BLOCK_IN)  ->  map_object objects (BLOCK_OUT / _EMPTY)  ->  writer objects (WRITER)
Plus SKIP (table_name not in data_loader) and FIRST_ROW (first loaded row's column types).
"""
import atexit
import os
import sys
from collections import Counter

ON = os.environ.get("LINKML_MAP_PROBE") == "1"
NO_COERCE = os.environ.get("LINKML_MAP_NO_COERCE") == "1"

BLOCK_IN = Counter()      # class_derivation -> primary rows streamed from the loader
BLOCK_OUT = Counter()     # class_derivation -> objects returned by map_object
BLOCK_OUT_EMPTY = Counter()  # class_derivation -> objects with <=1 non-None value (all-empty)
BLOCK_ERR = Counter()     # (class_derivation, err_type, cause) -> count  (must stay 0)
SKIP = {}                 # class_derivation -> (table_name, table_name in data_loader)
FIRST_ROW = {}            # table_name -> {column: type} of the first loaded row
WRITER = Counter()        # 'objects' -> total objects handed to the stream writer


def skip_check(name, table, in_loader):
    if ON:
        SKIP[name] = (table, bool(in_loader))


def block_row(name):
    if ON:
        BLOCK_IN[name] += 1


def first_row(table, row):
    if ON and table not in FIRST_ROW and isinstance(row, dict):
        FIRST_ROW[table] = {k: type(v).__name__ for k, v in row.items()}


def block_out(name, obj):
    if ON:
        BLOCK_OUT[name] += 1
        try:
            nonnull = sum(1 for v in obj.values() if v is not None)
        except AttributeError:
            nonnull = 2
        if nonnull <= 1:
            BLOCK_OUT_EMPTY[name] += 1


def block_error(name, err):
    if ON:
        cause = getattr(err, "__cause__", None)
        BLOCK_ERR[(name, type(err).__name__, type(cause).__name__ if cause else "-")] += 1


def writer_wrote(n):
    if ON:
        WRITER["objects"] += n


if ON:
    @atexit.register
    def _dump():
        p = lambda *a: print(*a, file=sys.stderr)  # noqa: E731
        p(f"\n===PROBE=== NO_COERCE={NO_COERCE}")
        p("===PROBE=== SKIP (class_derivation -> table, table_in_data_loader):")
        for k, v in sorted(SKIP.items()):
            p(f"  {k}: {v}")
        p("===PROBE=== STAGES (class_derivation: loader_in -> map_out (empty) -> [writer total below]):")
        for k in sorted(set(BLOCK_IN) | set(BLOCK_OUT)):
            p(f"  {k}: in={BLOCK_IN.get(k, 0)} map_out={BLOCK_OUT.get(k, 0)} map_empty={BLOCK_OUT_EMPTY.get(k, 0)}")
        p(f"===PROBE=== WRITER objects handed to stream writer (whole entity): {WRITER.get('objects', 0)}")
        p("===PROBE=== BLOCK ERRORS (must be empty): ")
        for k, v in sorted(BLOCK_ERR.items()):
            p(f"  {k}: {v}")
        p("===PROBE=== FIRST loaded row column types (table -> {col: type}):")
        for k, v in sorted(FIRST_ROW.items()):
            p(f"  {k}: {v}")
        p("===PROBE=== END")
