# my mappings

## Class Mappings


### Container `<-` Container

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |
| agents | | None |  persons  | . | . |

### Entity `<-` None

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |

### Agent `<-` Person

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |
| id | | None |  None  | . | . |
| label | | None |  name  | . | . |
| age | | None |  [expression]  | . | . |
| primary_email | | None |  None  | . | . |
| secondary_email | | None |  [expression]  | . | . |
| gender | | None |  [expression]  | . | . |
| driving_since | | None |  [expression]  | . | . |
| first_known_event | | None |  [expression]  | . | . |
| death_date | | None |  [expression]  | . | . |
| current_address | | None |  None  | . | . |
| has_familial_relationships | | None |  has_familial_relationships  | . | . |

### Job `<-` None

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |
| type | | None |  None  | . | . |
| current | | None |  [expression]  | . | . |

### Address `<-` Address

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |
| address_of | | None |  [expression]  | . | . |
| street | | None |  None  | . | . |
| city | | None |  None  | . | . |

### FamilialRelationship `<-` FamilialRelationship

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |
| type | | None |  None  | . | . |
| related_to | | None |  None  | . | . |

### SequenceFeature `<-` None

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |
| type | | None |  feature_type  | . | . |

### DenormMapping `<-` Mapping

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |
| id | | None |  None  | . | . |
| creator | | None |  None  | . | . |
| license | | None |  None  | . | . |
| subject_id | | None |  [expression]  | . | . |
| subject_name | | None |  [expression]  | . | . |
| object_id | | None |  [expression]  | . | . |
| object_name | | None |  [expression]  | . | . |
| predicate_id | | None |  predicate  | . | . |
| predicate_label | | None |  [expression]  | . | . |

## Enum Mappings


### Target enum MyFamilialRelationshipType

| Target | Source | Info |
| ------ | ------ | ---- |
| SIBLING_OF | SIBLING_OF | . |
| CHILD_OF | CHILD_OF | . |