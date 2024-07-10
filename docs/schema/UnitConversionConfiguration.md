

# Class: UnitConversionConfiguration



URI: [linkmltr:UnitConversionConfiguration](https://w3id.org/linkml/transformer/UnitConversionConfiguration)




```mermaid
 classDiagram
    class UnitConversionConfiguration
      UnitConversionConfiguration : source_magnitude_slot
        
          UnitConversionConfiguration --> None : source_magnitude_slot
        
      UnitConversionConfiguration : source_unit
        
          UnitConversionConfiguration --> None : source_unit
        
      UnitConversionConfiguration : source_unit_scheme
        
      UnitConversionConfiguration : source_unit_slot
        
          UnitConversionConfiguration --> None : source_unit_slot
        
      UnitConversionConfiguration : target_magnitude_slot
        
          UnitConversionConfiguration --> None : target_magnitude_slot
        
      UnitConversionConfiguration : target_unit
        
          UnitConversionConfiguration --> None : target_unit
        
      UnitConversionConfiguration : target_unit_scheme
        
      UnitConversionConfiguration : target_unit_slot
        
          UnitConversionConfiguration --> None : target_unit_slot
        
      
```




<!-- no inheritance hierarchy -->


## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [target_unit](target_unit.md) | 0..1 <br/> [String](String.md) |  | direct |
| [target_unit_scheme](target_unit_scheme.md) | 0..1 <br/> [String](String.md) |  | direct |
| [source_unit](source_unit.md) | 0..1 <br/> [String](String.md) |  | direct |
| [source_unit_scheme](source_unit_scheme.md) | 0..1 <br/> [String](String.md) |  | direct |
| [source_unit_slot](source_unit_slot.md) | 0..1 <br/> [String](String.md) |  | direct |
| [source_magnitude_slot](source_magnitude_slot.md) | 0..1 <br/> [String](String.md) |  | direct |
| [target_unit_slot](target_unit_slot.md) | 0..1 <br/> [String](String.md) |  | direct |
| [target_magnitude_slot](target_magnitude_slot.md) | 0..1 <br/> [String](String.md) |  | direct |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [SlotDerivation](SlotDerivation.md) | [unit_conversion](unit_conversion.md) | range | [UnitConversionConfiguration](UnitConversionConfiguration.md) |






## Identifier and Mapping Information







### Schema Source


* from schema: https://w3id.org/linkml/transformer





## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmltr:UnitConversionConfiguration |
| native | linkmltr:UnitConversionConfiguration |





## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: UnitConversionConfiguration
from_schema: https://w3id.org/linkml/transformer
attributes:
  target_unit:
    name: target_unit
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - UnitConversionConfiguration
  target_unit_scheme:
    name: target_unit_scheme
    examples:
    - value: ucum
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - UnitConversionConfiguration
    range: string
  source_unit:
    name: source_unit
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - UnitConversionConfiguration
  source_unit_scheme:
    name: source_unit_scheme
    examples:
    - value: ucum
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - UnitConversionConfiguration
    range: string
  source_unit_slot:
    name: source_unit_slot
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - UnitConversionConfiguration
  source_magnitude_slot:
    name: source_magnitude_slot
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - UnitConversionConfiguration
  target_unit_slot:
    name: target_unit_slot
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - UnitConversionConfiguration
  target_magnitude_slot:
    name: target_magnitude_slot
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - UnitConversionConfiguration

```
</details>

### Induced

<details>
```yaml
name: UnitConversionConfiguration
from_schema: https://w3id.org/linkml/transformer
attributes:
  target_unit:
    name: target_unit
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    alias: target_unit
    owner: UnitConversionConfiguration
    domain_of:
    - UnitConversionConfiguration
  target_unit_scheme:
    name: target_unit_scheme
    examples:
    - value: ucum
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    alias: target_unit_scheme
    owner: UnitConversionConfiguration
    domain_of:
    - UnitConversionConfiguration
    range: string
  source_unit:
    name: source_unit
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    alias: source_unit
    owner: UnitConversionConfiguration
    domain_of:
    - UnitConversionConfiguration
  source_unit_scheme:
    name: source_unit_scheme
    examples:
    - value: ucum
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    alias: source_unit_scheme
    owner: UnitConversionConfiguration
    domain_of:
    - UnitConversionConfiguration
    range: string
  source_unit_slot:
    name: source_unit_slot
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    alias: source_unit_slot
    owner: UnitConversionConfiguration
    domain_of:
    - UnitConversionConfiguration
  source_magnitude_slot:
    name: source_magnitude_slot
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    alias: source_magnitude_slot
    owner: UnitConversionConfiguration
    domain_of:
    - UnitConversionConfiguration
  target_unit_slot:
    name: target_unit_slot
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    alias: target_unit_slot
    owner: UnitConversionConfiguration
    domain_of:
    - UnitConversionConfiguration
  target_magnitude_slot:
    name: target_magnitude_slot
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    alias: target_magnitude_slot
    owner: UnitConversionConfiguration
    domain_of:
    - UnitConversionConfiguration

```
</details>