# LinkML-Map Compliance Suite

This is the output from running the full compliance test suite.

```yaml
Time_executed: 2026-08-06
Package: tests/test_compliance/test_compliance_suite.py
```

It is organized into **Feature Sets** that test a particular feature or group of features,
and **combinations** of different schemas, input objects, and transformation specifications.
This is intended to exhaustively test all combinations of features, and provide informative
output.

Each test is designed to demonstrate:

- data mapping (transformation)
- derived schemas
- inversion (reverse transformation) (in some cases)
- compilation to other frameworks (coming soon)

## Feature Set: test_map_types


Test mapping between basic data types.

This test uses an ultra-minimal schema with a single class and a single attribute,
the transformation specification maps that attribute onto itself, with a different
type, demonstrating type coercion.

Some cases will be trivially isomorphic (where `source_datatype` == `target_datatype`),
but these are executed anyway.

* **source_datatype**: linkml datatype of source object
* **target_datatype**: linkml datatype of target object
* **source_value**: value of source object
* **target_value**: expected value of slot in target object
* **invertible**: True if the transformation is invertible

### Combo: test_map_types[string-string-foo-foo-True]

Mapping `string` => `string`


Isomorphic mapping: input should equal output

**Source Schema**:


```yaml
name: types
description: Minimal single-attribute schema for testing datatype mapping
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: string

```

**Object Transformation**:

 * Source Object:
```yaml
s1: foo

```

 * Target Object:
```yaml
s1: foo

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: string

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: string

```

### Combo: test_map_types[integer-integer-5-5-True]

Mapping `integer` => `integer`


Isomorphic mapping: input should equal output

**Source Schema**:


```yaml
name: types
description: Minimal single-attribute schema for testing datatype mapping
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: integer

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: integer

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 5

```

 * Target Object:
```yaml
s1: 5

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: integer

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: integer

```

### Combo: test_map_types[string-integer-5-5-True]

Mapping `string` => `integer`


Should coerce datatype

**Source Schema**:


```yaml
name: types
description: Minimal single-attribute schema for testing datatype mapping
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: integer

```

**Object Transformation**:

 * Source Object:
```yaml
s1: '5'

```

 * Target Object:
```yaml
s1: 5

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: integer

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: string

```

### Combo: test_map_types[integer-float-5-5.0-True]

Mapping `integer` => `float`


Should coerce datatype

**Source Schema**:


```yaml
name: types
description: Minimal single-attribute schema for testing datatype mapping
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: integer

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: float

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 5

```

 * Target Object:
```yaml
s1: 5.0

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: integer

```

### Combo: test_map_types[float-integer-5.0-5-True]

Mapping `float` => `integer`


Should coerce datatype

**Source Schema**:


```yaml
name: types
description: Minimal single-attribute schema for testing datatype mapping
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: integer

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 5.0

```

 * Target Object:
```yaml
s1: 5

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: integer

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: float

```

### Combo: test_map_types[float-integer-5.2-5-False]

Mapping `float` => `integer`


Should coerce datatype

**Source Schema**:


```yaml
name: types
description: Minimal single-attribute schema for testing datatype mapping
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: integer

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 5.2

```

 * Target Object:
```yaml
s1: 5

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: integer

```

### Combo: test_map_types[integer-boolean-5-True-False]

Mapping `integer` => `boolean`


Should coerce datatype

**Source Schema**:


```yaml
name: types
description: Minimal single-attribute schema for testing datatype mapping
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: integer

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: boolean

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 5

```

 * Target Object:
```yaml
s1: true

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: boolean

```

### Combo: test_map_types[integer-boolean-0-False-False]

Mapping `integer` => `boolean`


Should coerce datatype

**Source Schema**:


```yaml
name: types
description: Minimal single-attribute schema for testing datatype mapping
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: integer

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      range: boolean

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 0

```

 * Target Object:
```yaml
s1: false

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: boolean

```

## Feature Set: test_map_collections


Test mapping between collection data types (lists and dicts).

This makes use of the `cast_collection_as` construct

* **source_datatype**: linkml datatype of source object
* **target_datatype**: linkml datatype of target object
* **source_value**: value of source object
* **target_value**: expected value of slot in target object
* **invertible**: True if the transformation is invertible

### Combo: test_map_collections[string-string-source_value0-target_value0-True]

Mapping `string` => `string`


Isomorphic mapping: **input must equal output**

**Source Schema**:


```yaml
name: types
description: Mapping between collection types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      ds:
        name: ds
        range: D
        multivalued: true
        inlined: true
        inlined_as_list: true
    tree_root: true
  D:
    name: D
    attributes:
      id:
        name: id
        identifier: true
      s1:
        name: s1
        range: string

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    ds:
      name: ds
      populated_from: ds
      cast_collection_as: MultiValuedDict
      dictionary_key: id
- name: D
  slot_derivations:
    id:
      name: id
      populated_from: id
    s1:
      name: s1
      populated_from: s1
      range: string

```

**Object Transformation**:

 * Source Object:
```yaml
ds:
- id: X
  s1: foo
- id: Y
  s1: bar

```

 * Target Object:
```yaml
ds:
  X:
    s1: foo
  Y:
    s1: bar

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      ds:
        name: ds
        domain_of:
        - C
        range: D
        multivalued: true
        inlined: true
        inlined_as_list: false
    tree_root: true
  D:
    name: D
    attributes:
      id:
        name: id
        identifier: true
        domain_of:
        - D
      s1:
        name: s1
        domain_of:
        - D
        range: string

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    ds:
      name: ds
      populated_from: ds
      cast_collection_as: MultiValuedList
- name: D
  populated_from: D
  slot_derivations:
    id:
      name: id
      populated_from: id
    s1:
      name: s1
      populated_from: s1
      range: string

```

### Combo: test_map_collections[string-string-source_value1-target_value1-True]

Mapping `string` => `string`


Isomorphic mapping: **input must equal output**

**Source Schema**:


```yaml
name: types
description: Mapping between collection types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      ds:
        name: ds
        range: D
        multivalued: true
        inlined: true
        inlined_as_list: false
    tree_root: true
  D:
    name: D
    attributes:
      id:
        name: id
        identifier: true
      s1:
        name: s1
        range: string

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    ds:
      name: ds
      populated_from: ds
      cast_collection_as: MultiValuedList
- name: D
  slot_derivations:
    id:
      name: id
      populated_from: id
    s1:
      name: s1
      populated_from: s1
      range: string

```

**Object Transformation**:

 * Source Object:
```yaml
ds:
  X:
    s1: foo
  Y:
    s1: bar

```

 * Target Object:
```yaml
ds:
- id: X
  s1: foo
- id: Y
  s1: bar

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      ds:
        name: ds
        domain_of:
        - C
        range: D
        multivalued: true
        inlined: true
        inlined_as_list: true
    tree_root: true
  D:
    name: D
    attributes:
      id:
        name: id
        identifier: true
        domain_of:
        - D
      s1:
        name: s1
        domain_of:
        - D
        range: string

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    ds:
      name: ds
      populated_from: ds
      cast_collection_as: MultiValuedDict
      dictionary_key: id
- name: D
  populated_from: D
  slot_derivations:
    id:
      name: id
      populated_from: id
    s1:
      name: s1
      populated_from: s1
      range: string

```

## Feature Set: test_expr


Test transformation using pythonic expressions.

This test uses a simple source schema with two slots (`s1` and `s2`).
These are combined using a pythonic expression, to populate the only
slot in the target schema (called `derived`).

The values of `s1` and `s2` can be numbers or strings.

If the expression wraps a slot in `{...}` then the presence of a None
forces the entire expression to be `None`

Limitations: At this time, the framework cannot generate a complete
derived schema or inversion for expressions. This will be fixed
in future.

- See also: [LinkML Expressions](https://linkml.io/linkml/schemas/expression-language.html)

* **expr**: pythonic expression
* **source_object**: source object
* **target_value**: expected value of slot in target object

### Combo: test_expr[s1 + s2-source_object0-11]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: integer
      s2:
        name: s2
        range: integer
    tree_root: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    derived:
      name: derived
      expr: s1 + s2

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 5
s2: 6

```

 * Target Object:
```yaml
derived: 11

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    attributes:
      derived:
        name: derived
    tree_root: true

```

### Combo: test_expr[{s1} + {s2}-source_object1-11]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: integer
      s2:
        name: s2
        range: integer
    tree_root: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    derived:
      name: derived
      expr: '{s1} + {s2}'

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 5
s2: 6

```

 * Target Object:
```yaml
derived: 11

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    attributes:
      derived:
        name: derived
    tree_root: true

```

### Combo: test_expr[{s1} + {s2}-source_object2-None]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: integer
    tree_root: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    derived:
      name: derived
      expr: '{s1} + {s2}'

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 5

```

 * Target Object:
```yaml
{}

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    attributes:
      derived:
        name: derived
    tree_root: true

```

### Combo: test_expr[s1 + s2.s3-source_object3-11]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: integer
      s2:
        name: s2
        range: D
    tree_root: true
  D:
    name: D
    attributes:
      s3:
        name: s3
        range: integer

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    derived:
      name: derived
      expr: s1 + s2.s3

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 5
s2:
  s3: 6

```

 * Target Object:
```yaml
derived: 11

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    attributes:
      derived:
        name: derived
    tree_root: true

```

### Combo: test_expr[s1 + s2.s3.s4-source_object4-11]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: integer
      s2:
        name: s2
        range: D
    tree_root: true
  D:
    name: D
    attributes:
      s4:
        name: s4
        range: integer
      s3:
        name: s3
        range: D

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    derived:
      name: derived
      expr: s1 + s2.s3.s4

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 5
s2:
  s3:
    s4: 6

```

 * Target Object:
```yaml
derived: 11

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    attributes:
      derived:
        name: derived
    tree_root: true

```

### Combo: test_expr[s1 + s2-source_object5-ab]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string
      s2:
        name: s2
        range: string
    tree_root: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    derived:
      name: derived
      expr: s1 + s2

```

**Object Transformation**:

 * Source Object:
```yaml
s1: a
s2: b

```

 * Target Object:
```yaml
derived: ab

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    attributes:
      derived:
        name: derived
    tree_root: true

```

### Combo: test_expr[s1 + s2-source_object6-target_value6]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string
        multivalued: true
      s2:
        name: s2
        range: string
        multivalued: true
    tree_root: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    derived:
      name: derived
      expr: s1 + s2

```

**Object Transformation**:

 * Source Object:
```yaml
s1:
- a
s2:
- b

```

 * Target Object:
```yaml
derived:
- a
- b

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    attributes:
      derived:
        name: derived
    tree_root: true

```

### Combo: test_expr[len(s1)-source_object7-1]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string
        multivalued: true
    tree_root: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    derived:
      name: derived
      expr: len(s1)

```

**Object Transformation**:

 * Source Object:
```yaml
s1:
- a

```

 * Target Object:
```yaml
derived: 1

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    attributes:
      derived:
        name: derived
    tree_root: true

```

### Combo: test_expr[s1 < s2-source_object8-True]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: integer
      s2:
        name: s2
        range: integer
    tree_root: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    derived:
      name: derived
      expr: s1 < s2

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 5
s2: 6

```

 * Target Object:
```yaml
derived: true

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    attributes:
      derived:
        name: derived
    tree_root: true

```

## Feature Set: test_simple_unit_conversion


Test unit conversion.

This test uses a simple source schema with a single class and a single attribute, where the attribute
is described using the [units](https://w3id.org/linkml/units) metaslot.

The recommended way to describe unit slots in LinkML is with UCUM, but a number of other schemes
can be used. We explicitly test for some known cases where UCUM uses non-standard units (e.g. Cel, mo),
as well as UCUM-specific syntax (e.g. `m.s-1`) and extensions (e.g. using annotations like `{Cre}`).

* **source_slot**: name of slot in source schema
* **target_slot**: name of slot in target schema
* **source_unit**: unit of source slot
* **target_unit**: unit of target slot
* **source_value**: magnitude of source slot (to be converted)
* **target_value**: expected magnitude of target slot (output of conversion)
* **err**:

### Combo: test_simple_unit_conversion[s1-s1-m-cm-ucum_code-1.0-100.0-None-None]

Unit Conversion: `1.0` `m` => `100.0` `cm` [with s1]


**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float
        unit:
          ucum_code: m

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: cm

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 1.0

```

 * Target Object:
```yaml
s1: 100.0

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float
        unit:
          ucum_code: cm

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: m
        target_unit_scheme: ucum_code
        source_unit: cm

```

### Combo: test_simple_unit_conversion[s1-s1-m-cm-symbol-1.0-100.0-None-None]

Unit Conversion: `1.0` `m` => `100.0` `cm` [with s1]


**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float
        unit:
          symbol: m

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: cm

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 1.0

```

 * Target Object:
```yaml
s1: 100.0

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float
        unit:
          ucum_code: cm

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: m
        target_unit_scheme: symbol
        source_unit: cm

```

### Combo: test_simple_unit_conversion[s1-s1-m-m-ucum_code-1.0-1.0-None-None]

Unit Conversion: `1.0` `m` => `1.0` `m` [with s1]


Isomorphic mapping: **input must equal output**
**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float
        unit:
          ucum_code: m

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: m

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 1.0

```

 * Target Object:
```yaml
s1: 1.0

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float
        unit:
          ucum_code: m

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: m
        target_unit_scheme: ucum_code
        source_unit: m

```

### Combo: test_simple_unit_conversion[s1-s1-a-mo-ucum_code-10.0-120.0-None-None]

Unit Conversion: `10.0` `a` => `120.0` `mo` [with s1]


**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float
        unit:
          ucum_code: a

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: mo

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 10.0

```

 * Target Object:
```yaml
s1: 120.0

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float
        unit:
          ucum_code: mo

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: a
        target_unit_scheme: ucum_code
        source_unit: mo

```

### Combo: test_simple_unit_conversion[s1-s1-a-mo-symbol-10.0-None-UndefinedUnitError-None]

Unit Conversion: `10.0` `a` => `None` `mo` [with s1]


**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float
        unit:
          symbol: a

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: mo

```

**Object Transformation**:

**Expected Error**: UndefinedUnitError
 * Source Object:
```yaml
s1: 10.0

```

 * Target Object:
```yaml
null
...

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float
        unit:
          ucum_code: mo

```

### Combo: test_simple_unit_conversion[s1-s1-m-ml-ucum_code-1.0-None-DimensionalityError-None]

Unit Conversion: `1.0` `m` => `None` `ml` [with s1]


**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float
        unit:
          ucum_code: m

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: ml

```

**Object Transformation**:

**Expected Error**: DimensionalityError
 * Source Object:
```yaml
s1: 1.0

```

 * Target Object:
```yaml
null
...

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float
        unit:
          ucum_code: ml

```

### Combo: test_simple_unit_conversion[s1-s1-m-pinknoodles-ucum_code-1.0-None-UndefinedUnitError-None]

Unit Conversion: `1.0` `m` => `None` `pinknoodles` [with s1]


**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float
        unit:
          ucum_code: m

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: pinknoodles

```

**Object Transformation**:

**Expected Error**: UndefinedUnitError
 * Source Object:
```yaml
s1: 1.0

```

 * Target Object:
```yaml
null
...

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float
        unit:
          ucum_code: pinknoodles

```

### Combo: test_simple_unit_conversion[s1-s1-ml-m-ucum_code-1.0-None-DimensionalityError-None]

Unit Conversion: `1.0` `ml` => `None` `m` [with s1]


**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float
        unit:
          ucum_code: ml

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: m

```

**Object Transformation**:

**Expected Error**: DimensionalityError
 * Source Object:
```yaml
s1: 1.0

```

 * Target Object:
```yaml
null
...

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float
        unit:
          ucum_code: m

```

### Combo: test_simple_unit_conversion[s1-s1-pinknoodles-m-ucum_code-1.0-None-UndefinedUnitError-None]

Unit Conversion: `1.0` `pinknoodles` => `None` `m` [with s1]


**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float
        unit:
          ucum_code: pinknoodles

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: m

```

**Object Transformation**:

**Expected Error**: UndefinedUnitError
 * Source Object:
```yaml
s1: 1.0

```

 * Target Object:
```yaml
null
...

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float
        unit:
          ucum_code: m

```

### Combo: test_simple_unit_conversion[s1-s1-m/s-cm/s-ucum_code-1.0-100.0-None-None]

Unit Conversion: `1.0` `m/s` => `100.0` `cm/s` [with s1]


**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float
        unit:
          ucum_code: m/s

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: cm/s

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 1.0

```

 * Target Object:
```yaml
s1: 100.0

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float
        unit:
          ucum_code: cm/s

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: m/s
        target_unit_scheme: ucum_code
        source_unit: cm/s

```

### Combo: test_simple_unit_conversion[s1-s1-m.s-1-cm.s-1-ucum_code-1.0-100.0-None-None]

Unit Conversion: `1.0` `m.s-1` => `100.0` `cm.s-1` [with s1]


**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float
        unit:
          ucum_code: m.s-1

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: cm.s-1

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 1.0

```

 * Target Object:
```yaml
s1: 100.0

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float
        unit:
          ucum_code: cm.s-1

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: m.s-1
        target_unit_scheme: ucum_code
        source_unit: cm.s-1

```

### Combo: test_simple_unit_conversion[s1-s1-g.m2-1-kg.m2-1-ucum_code-1.0-0.001-None-https://github.com/dalito/ucumvert/issues/8]

### Combo: test_simple_unit_conversion[height_in_m-height_in_cm-m-cm-ucum_code-1.0-100.0-None-None]

Unit Conversion: `1.0` `m` => `100.0` `cm` [with height_in_m]


**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      height_in_m:
        name: height_in_m
        range: float
        unit:
          ucum_code: m

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    height_in_cm:
      name: height_in_cm
      populated_from: height_in_m
      unit_conversion:
        target_unit: cm

```

**Object Transformation**:

 * Source Object:
```yaml
height_in_m: 1.0

```

 * Target Object:
```yaml
height_in_cm: 100.0

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      height_in_cm:
        name: height_in_cm
        domain_of:
        - C
        range: float
        unit:
          ucum_code: cm

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    height_in_m:
      name: height_in_m
      populated_from: height_in_cm
      unit_conversion:
        target_unit: m
        target_unit_scheme: ucum_code
        source_unit: cm

```

### Combo: test_simple_unit_conversion[s1-s1-m[H2O]{35Cel}-m[H2O]{35Cel}-ucum_code-1.0-1.0-None-None]

Unit Conversion: `1.0` `m[H2O]{35Cel}` => `1.0` `m[H2O]{35Cel}` [with s1]


Isomorphic mapping: **input must equal output**
**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: float
        unit:
          ucum_code: m[H2O]{35Cel}

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: m[H2O]{35Cel}

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 1.0

```

 * Target Object:
```yaml
s1: 1.0

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: float
        unit:
          ucum_code: m[H2O]{35Cel}

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
      unit_conversion:
        target_unit: m[H2O]{35Cel}
        target_unit_scheme: ucum_code
        source_unit: m[H2O]{35Cel}

```

## Feature Set: test_complex_unit_conversion


Test unit conversion, from complex object to simple scalar.

An example complex object would be an object with separate attributes for
representing magnitude (value) and unit.

For example `magnitude: 1.0, unit: "m"`

* **source_unit**: unit of source slot
* **target_unit**: unit of target slot
* **source_value**: magnitude of source slot (to be converted)
* **target_value**: expected magnitude of target slot (output of conversion)
* **roundtrip_object**: expected value of passing target object back through inverted transformation
* **err**: True if expected to raise an Error

### Combo: test_complex_unit_conversion[m-cm-1.0-100.0-roundtrip_object0-None]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  Q:
    name: Q
    attributes:
      magnitude:
        name: magnitude
        range: float
      unit:
        name: unit
        range: string
  C:
    name: C
    attributes:
      q:
        name: q
        range: Q
    tree_root: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: D
  populated_from: C
  slot_derivations:
    q_in_cm:
      name: q_in_cm
      populated_from: q
      unit_conversion:
        target_unit: cm
        source_unit_slot: unit
        source_magnitude_slot: magnitude

```

**Object Transformation**:

 * Source Object:
```yaml
q:
  magnitude: 1.0
  unit: m

```

 * Target Object:
```yaml
q_in_cm: 100.0

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  D:
    name: D
    attributes:
      q_in_cm:
        name: q_in_cm
        domain_of:
        - C
        range: Q
        unit:
          ucum_code: cm
    tree_root: true

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: D
  slot_derivations:
    q:
      name: q
      populated_from: q_in_cm
      unit_conversion:
        source_unit: cm
        target_unit_slot: unit
        target_magnitude_slot: magnitude

```

### Combo: test_complex_unit_conversion[cm-cm-100.0-100.0-roundtrip_object1-None]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  Q:
    name: Q
    attributes:
      magnitude:
        name: magnitude
        range: float
      unit:
        name: unit
        range: string
  C:
    name: C
    attributes:
      q:
        name: q
        range: Q
    tree_root: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: D
  populated_from: C
  slot_derivations:
    q_in_cm:
      name: q_in_cm
      populated_from: q
      unit_conversion:
        target_unit: cm
        source_unit_slot: unit
        source_magnitude_slot: magnitude

```

**Object Transformation**:

 * Source Object:
```yaml
q:
  magnitude: 100.0
  unit: cm

```

 * Target Object:
```yaml
q_in_cm: 100.0

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  D:
    name: D
    attributes:
      q_in_cm:
        name: q_in_cm
        domain_of:
        - C
        range: Q
        unit:
          ucum_code: cm
    tree_root: true

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: D
  slot_derivations:
    q:
      name: q
      populated_from: q_in_cm
      unit_conversion:
        source_unit: cm
        target_unit_slot: unit
        target_magnitude_slot: magnitude

```

### Combo: test_complex_unit_conversion[cm-ml-100.0-None-None-DimensionalityError]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  Q:
    name: Q
    attributes:
      magnitude:
        name: magnitude
        range: float
      unit:
        name: unit
        range: string
  C:
    name: C
    attributes:
      q:
        name: q
        range: Q
    tree_root: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: D
  populated_from: C
  slot_derivations:
    q_in_ml:
      name: q_in_ml
      populated_from: q
      unit_conversion:
        target_unit: ml
        source_unit_slot: unit
        source_magnitude_slot: magnitude

```

**Object Transformation**:

**Expected Error**: DimensionalityError
 * Source Object:
```yaml
q:
  magnitude: 100.0
  unit: cm

```

 * Target Object:
```yaml
null
...

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  D:
    name: D
    attributes:
      q_in_ml:
        name: q_in_ml
        domain_of:
        - C
        range: Q
        unit:
          ucum_code: ml
    tree_root: true

```

### Combo: test_complex_unit_conversion[cm-pinknoodles-100.0-None-None-UndefinedUnitError]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  Q:
    name: Q
    attributes:
      magnitude:
        name: magnitude
        range: float
      unit:
        name: unit
        range: string
  C:
    name: C
    attributes:
      q:
        name: q
        range: Q
    tree_root: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: D
  populated_from: C
  slot_derivations:
    q_in_pinknoodles:
      name: q_in_pinknoodles
      populated_from: q
      unit_conversion:
        target_unit: pinknoodles
        source_unit_slot: unit
        source_magnitude_slot: magnitude

```

**Object Transformation**:

**Expected Error**: UndefinedUnitError
 * Source Object:
```yaml
q:
  magnitude: 100.0
  unit: cm

```

 * Target Object:
```yaml
null
...

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  D:
    name: D
    attributes:
      q_in_pinknoodles:
        name: q_in_pinknoodles
        domain_of:
        - C
        range: Q
        unit:
          ucum_code: pinknoodles
    tree_root: true

```

## Feature Set: test_stringify


Test compaction of multivalued slots into a string.

Stringification is primarily intended for mapping from complex nested formats to
simple tabular TSV formats, where some of the following methodologies can be used:

- flattening lists using an (internal) delimiter
- flattening lists or more complex objects using JSON or YAML

For example, `["a", "b"]` => `"a,b"`

As a convention we use `s1_verbatim` as a slot/attribute name for the
stringified form.

* **syntax**: SerializationSyntaxType
* **delimiter**: delimiter to use in stringification
* **source_value**: source value (a list)
* **target_value**: expected value of slot in target object (a string)

### Combo: test_stringify[None-,-source_value0-a,b]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string
        multivalued: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: D
  populated_from: C
  slot_derivations:
    s1_verbatim:
      name: s1_verbatim
      populated_from: s1
      stringification:
        delimiter: ','

```

**Object Transformation**:

 * Source Object:
```yaml
s1:
- a
- b

```

 * Target Object:
```yaml
s1_verbatim: a,b

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  D:
    name: D
    attributes:
      s1_verbatim:
        name: s1_verbatim
        domain_of:
        - C
        range: string
        multivalued: false

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: D
  slot_derivations:
    s1:
      name: s1
      populated_from: s1_verbatim
      stringification:
        delimiter: ','
        reversed: true

```

**Compiled Specification (SQLCompiler)**:


INSERT INTO D SELECT
  STRING_AGG(s1, ',') AS s1_verbatim FROM C;

### Combo: test_stringify[None-|-source_value1-a|b]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string
        multivalued: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: D
  populated_from: C
  slot_derivations:
    s1_verbatim:
      name: s1_verbatim
      populated_from: s1
      stringification:
        delimiter: '|'

```

**Object Transformation**:

 * Source Object:
```yaml
s1:
- a
- b

```

 * Target Object:
```yaml
s1_verbatim: a|b

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  D:
    name: D
    attributes:
      s1_verbatim:
        name: s1_verbatim
        domain_of:
        - C
        range: string
        multivalued: false

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: D
  slot_derivations:
    s1:
      name: s1
      populated_from: s1_verbatim
      stringification:
        delimiter: '|'
        reversed: true

```

**Compiled Specification (SQLCompiler)**:


INSERT INTO D SELECT
  STRING_AGG(s1, '|') AS s1_verbatim FROM C;

### Combo: test_stringify[None-|-source_value2-a]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string
        multivalued: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: D
  populated_from: C
  slot_derivations:
    s1_verbatim:
      name: s1_verbatim
      populated_from: s1
      stringification:
        delimiter: '|'

```

**Object Transformation**:

 * Source Object:
```yaml
s1:
- a

```

 * Target Object:
```yaml
s1_verbatim: a

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  D:
    name: D
    attributes:
      s1_verbatim:
        name: s1_verbatim
        domain_of:
        - C
        range: string
        multivalued: false

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: D
  slot_derivations:
    s1:
      name: s1
      populated_from: s1_verbatim
      stringification:
        delimiter: '|'
        reversed: true

```

**Compiled Specification (SQLCompiler)**:


INSERT INTO D SELECT
  STRING_AGG(s1, '|') AS s1_verbatim FROM C;

### Combo: test_stringify[None-|-source_value3-]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string
        multivalued: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: D
  populated_from: C
  slot_derivations:
    s1_verbatim:
      name: s1_verbatim
      populated_from: s1
      stringification:
        delimiter: '|'

```

**Object Transformation**:

 * Source Object:
```yaml
{}

```

 * Target Object:
```yaml
s1_verbatim: ''

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  D:
    name: D
    attributes:
      s1_verbatim:
        name: s1_verbatim
        domain_of:
        - C
        range: string
        multivalued: false

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: D
  slot_derivations:
    s1:
      name: s1
      populated_from: s1_verbatim
      stringification:
        delimiter: '|'
        reversed: true

```

**Compiled Specification (SQLCompiler)**:


INSERT INTO D SELECT
  STRING_AGG(s1, '|') AS s1_verbatim FROM C;

### Combo: test_stringify[JSON-None-source_value4-["a", "b"]]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string
        multivalued: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: D
  populated_from: C
  slot_derivations:
    s1_verbatim:
      name: s1_verbatim
      populated_from: s1
      stringification:
        syntax: JSON

```

**Object Transformation**:

 * Source Object:
```yaml
s1:
- a
- b

```

 * Target Object:
```yaml
s1_verbatim: '["a", "b"]'

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  D:
    name: D
    attributes:
      s1_verbatim:
        name: s1_verbatim
        domain_of:
        - C
        range: string
        multivalued: false

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: D
  slot_derivations:
    s1:
      name: s1
      populated_from: s1_verbatim
      stringification:
        reversed: true
        syntax: JSON

```

**Compiled Specification (SQLCompiler)**:


INSERT INTO D SELECT
  CAST(s1 AS TEXT) AS s1_verbatim FROM C;

### Combo: test_stringify[JSON-None-source_value5-[]]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string
        multivalued: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: D
  populated_from: C
  slot_derivations:
    s1_verbatim:
      name: s1_verbatim
      populated_from: s1
      stringification:
        syntax: JSON

```

**Object Transformation**:

 * Source Object:
```yaml
{}

```

 * Target Object:
```yaml
s1_verbatim: '[]'

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  D:
    name: D
    attributes:
      s1_verbatim:
        name: s1_verbatim
        domain_of:
        - C
        range: string
        multivalued: false

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: D
  slot_derivations:
    s1:
      name: s1
      populated_from: s1_verbatim
      stringification:
        reversed: true
        syntax: JSON

```

**Compiled Specification (SQLCompiler)**:


INSERT INTO D SELECT
  CAST(s1 AS TEXT) AS s1_verbatim FROM C;

### Combo: test_stringify[YAML-None-source_value6-[a, b]]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string
        multivalued: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: D
  populated_from: C
  slot_derivations:
    s1_verbatim:
      name: s1_verbatim
      populated_from: s1
      stringification:
        syntax: YAML

```

**Object Transformation**:

 * Source Object:
```yaml
s1:
- a
- b

```

 * Target Object:
```yaml
s1_verbatim: '[a, b]'

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  D:
    name: D
    attributes:
      s1_verbatim:
        name: s1_verbatim
        domain_of:
        - C
        range: string
        multivalued: false

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: D
  slot_derivations:
    s1:
      name: s1
      populated_from: s1_verbatim
      stringification:
        reversed: true
        syntax: YAML

```

**Compiled Specification (SQLCompiler)**:


INSERT INTO D SELECT
  s1 AS s1_verbatim FROM C;

## Feature Set: test_isomorphic


Test mapping a schema to an identical schema (i.e copy).

This also tests for the ability to recursively descend a nested structure.

* **source_object**:
* **use_expr**:
* **supply_source_schema**: TODO: always True for now

### Combo: test_isomorphic[True-True-source_object0]

**Source Schema**:


```yaml
name: isomorphic
id: isomorphic
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  Container:
    name: Container
    attributes:
      c_list:
        name: c_list
        range: C
        multivalued: true
      d:
        name: d
        range: D
    tree_root: true
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string
      s2:
        name: s2
        range: string
  D:
    name: D
    attributes:
      s3:
        name: s3
        range: string

```

**Transformer Specification**:


```yaml
class_derivations:
- name: Container
  populated_from: Container
  slot_derivations:
    c_list:
      name: c_list
      populated_from: c_list
      range: C
    d:
      name: d
      populated_from: d
      range: D
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
    s2:
      name: s2
      populated_from: s2
- name: D
  populated_from: D
  slot_derivations:
    s3:
      name: s3
      expr: s3

```

**Object Transformation**:

 * Source Object:
```yaml
c_list:
- s1: a
  s2: b
- s1: c
  s2: d
d:
  s3: e

```

 * Target Object:
```yaml
c_list:
- s1: a
  s2: b
- s1: c
  s2: d
d:
  s3: e

```

**Target Schema (Derived)**:


```yaml
name: isomorphic-derived
id: isomorphic-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: isomorphic-derived/
classes:
  Container:
    name: Container
    attributes:
      c_list:
        name: c_list
        domain_of:
        - Container
        range: C
        multivalued: true
      d:
        name: d
        domain_of:
        - Container
        range: D
    tree_root: true
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: string
      s2:
        name: s2
        domain_of:
        - C
        range: string
  D:
    name: D
    attributes:
      s3:
        name: s3
        domain_of:
        - D
        range: string

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: Container
  populated_from: Container
  slot_derivations:
    c_list:
      name: c_list
      populated_from: c_list
      range: C
    d:
      name: d
      populated_from: d
      range: D
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
    s2:
      name: s2
      populated_from: s2
- name: D
  populated_from: D
  slot_derivations:
    s3:
      name: s3
      populated_from: s3

```

### Combo: test_isomorphic[True-False-source_object0]

**Source Schema**:


```yaml
name: isomorphic
id: isomorphic
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  Container:
    name: Container
    attributes:
      c_list:
        name: c_list
        range: C
        multivalued: true
      d:
        name: d
        range: D
    tree_root: true
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: string
      s2:
        name: s2
        range: string
  D:
    name: D
    attributes:
      s3:
        name: s3
        range: string

```

**Transformer Specification**:


```yaml
class_derivations:
- name: Container
  populated_from: Container
  slot_derivations:
    c_list:
      name: c_list
      populated_from: c_list
      range: C
    d:
      name: d
      populated_from: d
      range: D
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
    s2:
      name: s2
      populated_from: s2
- name: D
  populated_from: D
  slot_derivations:
    s3:
      name: s3
      populated_from: s3

```

**Object Transformation**:

 * Source Object:
```yaml
c_list:
- s1: a
  s2: b
- s1: c
  s2: d
d:
  s3: e

```

 * Target Object:
```yaml
c_list:
- s1: a
  s2: b
- s1: c
  s2: d
d:
  s3: e

```

**Target Schema (Derived)**:


```yaml
name: isomorphic-derived
id: isomorphic-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: isomorphic-derived/
classes:
  Container:
    name: Container
    attributes:
      c_list:
        name: c_list
        domain_of:
        - Container
        range: C
        multivalued: true
      d:
        name: d
        domain_of:
        - Container
        range: D
    tree_root: true
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: string
      s2:
        name: s2
        domain_of:
        - C
        range: string
  D:
    name: D
    attributes:
      s3:
        name: s3
        domain_of:
        - D
        range: string

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: Container
  populated_from: Container
  slot_derivations:
    c_list:
      name: c_list
      populated_from: c_list
      range: C
    d:
      name: d
      populated_from: d
      range: D
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
    s2:
      name: s2
      populated_from: s2
- name: D
  populated_from: D
  slot_derivations:
    s3:
      name: s3
      populated_from: s3

```

## Feature Set: test_join


Test joining two objects into a single object, aka denormalization.

* **source_object**: normalized source object
* **target_object**: denormalized target object
* **inlined**: True if the source objects are inlined

### Combo: test_join[source_object0-target_object0-True]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  R:
    name: R
    attributes:
      s1:
        name: s1
        range: E
        inlined: true
      s2:
        name: s2
        range: E
        inlined: true
    tree_root: true
  E:
    name: E
    attributes:
      id:
        name: id
        identifier: true
        range: string
      name:
        name: name
        range: string

```

**Transformer Specification**:


```yaml
class_derivations:
- name: R
  populated_from: R
  slot_derivations:
    s1_id:
      name: s1_id
      expr: s1.id
    s1_name:
      name: s1_name
      expr: s1.name
    s2_id:
      name: s2_id
      expr: s2.id
    s2_name:
      name: s2_name
      expr: s2.name

```

**Object Transformation**:

 * Source Object:
```yaml
s1:
  id: x1
  name: foo
s2:
  id: x2
  name: bar

```

 * Target Object:
```yaml
s1_id: x1
s1_name: foo
s2_id: x2
s2_name: bar

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  R:
    name: R
    attributes:
      s1_id:
        name: s1_id
      s1_name:
        name: s1_name
      s2_id:
        name: s2_id
      s2_name:
        name: s2_name
    tree_root: true

```

### Combo: test_join[source_object0-target_object0-False]

**Source Schema**:


```yaml
name: types
id: types
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  R:
    name: R
    attributes:
      s1:
        name: s1
        range: E
        inlined: false
      s2:
        name: s2
        range: E
        inlined: false
    tree_root: false
  E:
    name: E
    attributes:
      id:
        name: id
        identifier: true
        range: string
      name:
        name: name
        range: string
  Container:
    name: Container
    attributes:
      r_list:
        name: r_list
        range: R
        multivalued: true
      e_list:
        name: e_list
        range: E
        multivalued: true
        inlined_as_list: true
    tree_root: true

```

**Transformer Specification**:


```yaml
class_derivations:
- name: R
  populated_from: R
  slot_derivations:
    s1_id:
      name: s1_id
      expr: s1.id
    s1_name:
      name: s1_name
      expr: s1.name
    s2_id:
      name: s2_id
      expr: s2.id
    s2_name:
      name: s2_name
      expr: s2.name
- name: Container
  populated_from: Container
  slot_derivations:
    r_list:
      name: r_list
      populated_from: r_list

```

**Object Transformation**:

 * Source Object:
```yaml
r_list:
- s1: x1
  s2: x2
e_list:
- id: x1
  name: foo
- id: x2
  name: bar

```

 * Target Object:
```yaml
r_list:
- s1_id: x1
  s1_name: foo
  s2_id: x2
  s2_name: bar

```

**Target Schema (Derived)**:


```yaml
name: types-derived
id: types-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: types-derived/
classes:
  R:
    name: R
    attributes:
      s1_id:
        name: s1_id
      s1_name:
        name: s1_name
      s2_id:
        name: s2_id
      s2_name:
        name: s2_name
    tree_root: false
  Container:
    name: Container
    attributes:
      r_list:
        name: r_list
        domain_of:
        - Container
        range: R
        multivalued: true
    tree_root: true

```

## Feature Set: test_map_enum


Test mapping between enum values.

Currently this only supports simple dictionary-style mapping between permissible values,
akin to SSSOM, but in future additional expressivity will be supported, including:

- mapping ranges to categorical values
- boolean/branching logic

* **source_value**: source enum permissible value to be mapped
* **mapping**: mapping from source to target enum permissible values
* **target_value**: expected target enum permissible value

### Combo: test_map_enum[A-mapping0-B-False]

**Source Schema**:


```yaml
name: enums
id: enums
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
enums:
  E:
    name: E
    permissible_values:
      A:
        text: A
      B:
        text: B
      C:
        text: C
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: E

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
enum_derivations:
  E:
    name: E
    mirror_source: false
    populated_from: E
    permissible_value_derivations:
      B:
        name: B
        populated_from:
        - A

```

**Object Transformation**:

 * Source Object:
```yaml
s1: A

```

 * Target Object:
```yaml
s1: B

```

**Target Schema (Derived)**:


```yaml
name: enums-derived
id: enums-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: enums-derived/
enums:
  E:
    name: E
    permissible_values:
      A:
        text: A
      B:
        text: B
      C:
        text: C
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: E

```

**Inverted Transformation Specification** (Derived):


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
enum_derivations:
  E:
    name: E
    populated_from: E
    permissible_value_derivations:
      A:
        name: A
        populated_from:
        - B

```

### Combo: test_map_enum[Z-mapping1-None-False]

**Source Schema**:


```yaml
name: enums
id: enums
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
enums:
  E:
    name: E
    permissible_values:
      A:
        text: A
      B:
        text: B
      C:
        text: C
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: E

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
enum_derivations:
  E:
    name: E
    mirror_source: false
    populated_from: E
    permissible_value_derivations:
      B:
        name: B
        populated_from:
        - A

```

**Object Transformation**:

 * Source Object:
```yaml
s1: Z

```

 * Target Object:
```yaml
{}

```

**Target Schema (Derived)**:


```yaml
name: enums-derived
id: enums-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: enums-derived/
enums:
  E:
    name: E
    permissible_values:
      A:
        text: A
      B:
        text: B
      C:
        text: C
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: E

```

### Combo: test_map_enum[C-mapping2-C-True]

**Source Schema**:


```yaml
name: enums
id: enums
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
enums:
  E:
    name: E
    permissible_values:
      A:
        text: A
      B:
        text: B
      C:
        text: C
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: E

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
enum_derivations:
  E:
    name: E
    mirror_source: true
    populated_from: E
    permissible_value_derivations:
      B:
        name: B
        populated_from:
        - A

```

### Combo: test_map_enum[A-mapping3-B-False]

**Source Schema**:


```yaml
name: enums
id: enums
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
enums:
  E:
    name: E
    permissible_values:
      A:
        text: A
      B:
        text: B
      C:
        text: C
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: E

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
enum_derivations:
  E:
    name: E
    mirror_source: false
    populated_from: E
    permissible_value_derivations:
      B:
        name: B
        populated_from:
        - A
        - C

```

**Object Transformation**:

 * Source Object:
```yaml
s1: A

```

 * Target Object:
```yaml
s1: B

```

**Target Schema (Derived)**:


```yaml
name: enums-derived
id: enums-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: enums-derived/
enums:
  E:
    name: E
    permissible_values:
      A:
        text: A
      B:
        text: B
      C:
        text: C
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: E

```

### Combo: test_map_enum[C-mapping4-B-False]

**Source Schema**:


```yaml
name: enums
id: enums
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
enums:
  E:
    name: E
    permissible_values:
      A:
        text: A
      B:
        text: B
      C:
        text: C
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        range: E

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  slot_derivations:
    s1:
      name: s1
      populated_from: s1
enum_derivations:
  E:
    name: E
    mirror_source: false
    populated_from: E
    permissible_value_derivations:
      B:
        name: B
        populated_from:
        - A
        - C

```

**Object Transformation**:

 * Source Object:
```yaml
s1: C

```

 * Target Object:
```yaml
s1: B

```

**Target Schema (Derived)**:


```yaml
name: enums-derived
id: enums-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: enums-derived/
enums:
  E:
    name: E
    permissible_values:
      A:
        text: A
      B:
        text: B
      C:
        text: C
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: E

```

## Feature Set: test_inheritance


Test inheritance.

Transformation specifications can utilize inheritance, in the same way that LinkML schemas can.

* **is_a**: use is_as instead of mixins in test schema
* **flatten**: roll down inherited slots

### Combo: test_inheritance[False-True]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    is_a: D
    attributes:
      s1:
        name: s1
        range: integer
    tree_root: true
  D:
    name: D
    attributes:
      s2:
        name: s2
        range: integer

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  is_a: D
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      expr: s1 + 1
- name: D
  populated_from: D
  slot_derivations:
    s2:
      name: s2
      expr: s2 + 1

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 1
s2: 2

```

 * Target Object:
```yaml
s1: 2
s2: 3

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    is_a: D
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: integer
    tree_root: true
  D:
    name: D
    attributes:
      s2:
        name: s2
        domain_of:
        - D
        range: integer

```

### Combo: test_inheritance[False-False]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    mixins:
    - D
    attributes:
      s1:
        name: s1
        range: integer
    tree_root: true
  D:
    name: D
    attributes:
      s2:
        name: s2
        range: integer

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  mixins:
  - D
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      expr: s1 + 1
- name: D
  populated_from: D
  slot_derivations:
    s2:
      name: s2
      expr: s2 + 1

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 1
s2: 2

```

 * Target Object:
```yaml
s1: 2
s2: 3

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    mixins:
    - D
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: integer
    tree_root: true
  D:
    name: D
    attributes:
      s2:
        name: s2
        domain_of:
        - D
        range: integer

```

### Combo: test_inheritance[True-True]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    is_a: D
    attributes:
      s1:
        name: s1
        range: integer
    tree_root: true
  D:
    name: D
    attributes:
      s2:
        name: s2
        range: integer

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      expr: s1 + 1
    s2:
      name: s2
      expr: s2 + 1

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 1
s2: 2

```

 * Target Object:
```yaml
s1: 2
s2: 3

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: integer
      s2:
        name: s2
        domain_of:
        - D
        range: integer
    tree_root: true

```

### Combo: test_inheritance[True-False]

**Source Schema**:


```yaml
name: expr
id: expr
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: test
classes:
  C:
    name: C
    mixins:
    - D
    attributes:
      s1:
        name: s1
        range: integer
    tree_root: true
  D:
    name: D
    attributes:
      s2:
        name: s2
        range: integer

```

**Transformer Specification**:


```yaml
class_derivations:
- name: C
  populated_from: C
  slot_derivations:
    s1:
      name: s1
      expr: s1 + 1
    s2:
      name: s2
      expr: s2 + 1

```

**Object Transformation**:

 * Source Object:
```yaml
s1: 1
s2: 2

```

 * Target Object:
```yaml
s1: 2
s2: 3

```

**Target Schema (Derived)**:


```yaml
name: expr-derived
id: expr-derived
imports:
- linkml:types
prefixes:
  linkml:
    prefix_prefix: linkml
    prefix_reference: https://w3id.org/linkml/
  test:
    prefix_prefix: test
    prefix_reference: http://example.org/test/
default_prefix: expr-derived/
classes:
  C:
    name: C
    attributes:
      s1:
        name: s1
        domain_of:
        - C
        range: integer
      s2:
        name: s2
        domain_of:
        - D
        range: integer
    tree_root: true

```
