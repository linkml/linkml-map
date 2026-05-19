# PersonInfo to Agent example transformation

## Class Mappings


### Container `<-` Container

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |
| agents | | Agent |  persons  | . | . |

### Entity `<-` Entity

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |

### Agent `<-` Person

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |
| id | | None |  id  | . | . |
| label | | None |  name  | . | . |
| age | | None |  [expression]  | . | . |
| primary_email | | None |  primary_email  | . | . |
| secondary_email | | None |  [expression]  | . | . |
| gender | | None |  [expression]  | . | . |
| driving_since | | None |  [expression]  | . | . |
| first_known_event | | None |  [expression]  | . | . |
| death_date | | None |  [expression]  | . | . |
| current_address | | Address |  current_address  | . | . |
| has_familial_relationships | | FamilialRelationship |  has_familial_relationships  | . | . |

### Address `<-` Address

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |
| address_of | | None |  [expression]  | . | . |
| street | | None |  street  | . | . |
| city | | None |  city  | . | . |

### FamilialRelationship `<-` FamilialRelationship

| Target | Target Range | Source | Source Range | Info |
| ------ | ------ | ---- | ---- | ---- |
| type | | None |  type  | . | . |
| related_to | | Agent |  related_to  | . | . |

## Enum Mappings


### Target enum FamilialRelationshipType

| Target | Source | Info |
| ------ | ------ | ---- |
| SIBLING_OF | SIBLING_OF | . |
| CHILD_OF | CHILD_OF | . |