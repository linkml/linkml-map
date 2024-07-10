# Mapping Between LinkML Schemas

# Draft
2022-06-24

# Problem: map data from one schema to another

* Problem: Map d1 → d2
  * Assumption d1 and d2 conform to two separate schemas\, s1→ s2
* Sub\-problems:
  * Ingest/Import: my data warehouse conforms to s2 \(e\.g\. Monarch ingest\)
  * Export: make my data ingest friendly
  * Migrations: s1 and s2 are different versions of the same schema
* Not in scope: in\-schema syntactic or structural transforms
  * JSON to YAML\, JSON to TSV\, JSON to SQL\, JSON to RDF\, ORM\, …
  * In LinkML this is already largely solved
* The actual problem space is highly varied
  * S1 and S2 may be trivially isomorphic
  * S1 and S2 may differ in complex or nuanced ways

# There are many existing approaches

* Generic frameworks\, driven by declarative specification in Domain Specific Language \(DSL\)
* JSON\-based
  * Google whistle
  * _[jsonpath\-lift](https://www.npmjs.com/package/jsonpath-lifter)_
* XSLT
* Semweb
  * YARRML\, R2RML
* Many many more…
* Bespoke transforms: non\-declarative
* Implement in python/awk/etc\.
* Hybrid: bespoke with some declarative mappings in ad\-hoc format
* E\.g\. NMDC ingest framework

# Traps with declarative mapping

* Declarative is great\, until it’s not
* Anti\-patterns:
  * Insufficient expressivity to carry out real world tasks
  * Bolting on features to mapping DSL until it’s a fully\-featured Turing\-complete language
  * Optimization/scalability at mercy of framework
  * Messy layering between DSL and host language
    * It can be useful to leverage host language features \(e\.g arbitrary python function\)
    * But this can get confusing:
      * NFNF: Neither fish nor fowl
      * Limits optimizations \(forces iterative host language calls\)

# YARRRML

![](img/Mapping%20Between%20LinkML%20Schemas0.png)

<span style="color:#1A73E8"> _[https://rml\.io/yarrrml/](https://rml.io/yarrrml/)_ </span>

# YARRRML notes

* Has a playground\, which is great
* Mixes two concerns:
  * 1\. Isomorphic structural mapping between JSON/TSVs and RDF \(already covered by JSON\-LD\)
  * 2\. Mapping
  * This isn’t necessarily bad \- it’s quite practical\, but a little unsatisfying IMO

# jsonpath-lifter

![](img/Mapping%20Between%20LinkML%20Schemas1.png)

![](img/Mapping%20Between%20LinkML%20Schemas2.png)

![](img/Mapping%20Between%20LinkML%20Schemas3.png)

![](img/Mapping%20Between%20LinkML%20Schemas4.png)

![](img/Mapping%20Between%20LinkML%20Schemas5.png)

![](img/Mapping%20Between%20LinkML%20Schemas6.png)

![](img/Mapping%20Between%20LinkML%20Schemas7.png)

Was proposed for CCDH CRDC\-node mappings

Doesn’t seem widely used

Is there a big advantage over simply writing javascript functions?

# Koza (previously: bioweave)

![](img/Mapping%20Between%20LinkML%20Schemas8.png)

![](img/Mapping%20Between%20LinkML%20Schemas9.png)

# ETL frameworks

* There are many many ETL frameworks
  * E\.g\. WebKarma
* Inherently mixing of concerns
  * Here we are concerned with the “T” part
* Do existing frameworks separate out the T as a modular composable component?
  * I’m not sure

# Do we need Yet Another Mapping Framework?

* LinkML philosophy:
* Embrace\, extend\,  _parasitize_
* Develop lightweight ways to map
  * Map mappings to existing mapping frameworks
    * This actually makes sense even if it sounds kind of meta…

# Level 0 Mapping: Isomorphic, same URIs

classes:

Person:

class\_uri:  __sdo:Person__

attributes:

family\_name:

slot\_uri:  __sdo:familyName__

address:

slot\_uri:  __sdo:address__

classes:

Agent:

class\_uri:  __sdo:Person__

attributes:

surname:

slot\_uri:  __sdo:familyName__

home\_address:

slot\_uri:  __sdo:address__

family\_name: Wu

address: 1 my street\, Oakville

surname: Wu

home\_address: 1 my street\, Oakville

# Level 0: handled by standard linkml convert to/from RDF

classes:

Person:

class\_uri:  __sdo:Person__

attributes:

family\_name:

slot\_uri:  __sdo:familyName__

address:

slot\_uri:  __sdo:address__

classes:

Agent:

class\_uri:  __sdo:Person__

attributes:

surname:

slot\_uri:  __sdo:familyName__

home\_address:

slot\_uri:  __sdo:address__

_data2 \(yaml/json\)_

_d_  _ata1 \(yaml/json\)_

family\_name: Wu

address: 1 my street\, Oakville

surname: Wu

home\_address: 1 my street\, Oakville

_d_  _ata1\.ttl == data2\.ttl_

\[sdo:familyName “Wu” ;

sdo:address “1 my street\, Oakville”

\]

# Level 0: Enums TODO: add example here. Basically this works the same way

# Level 0: HOWTO

Compose two commands:

linkml\-convert \-s schema1\.yaml data1\.yaml \-o data1\.ttl

linkml\-convert \-s schema2\.yaml data1\.ttl \-o data2\.yaml

That’s it\!

TODO:

Write a wrapper \(linkml\-map\-data?\) that does this in one command

# Level 0: other considerations

* Going via RDF in theory eliminates inlining differences
  * E\.g\. s1 inlines address objects\, s2 uses references \(inlined: false\) and includes a separate index slot for addresses
* Current status:
  * Currently when going from s1 to s2\, no index slots are generated
  * This could be done as part of the general rdflib framework

# Lessons learned so far: annotate your schema with URIs!

* Annotating schemas with URIs is  _optional_  with LinkML
  * But your future self and data users will thank you for careful schema annotation\!
* Hints:
  * Schema\-automator can provide suggestions for your element and enum URIs
  * Sometimes plain semweb URIs \(e\.g\. schema\.org\) can be easier for interoperation than overly granular OBO ones
    * E\.g modeling Personhood as a  _role_  vs straightforward schema:Person

# Level 1 Mapping: Isomorphic, different URIs

name: example\-semweb\-schema

classes:

Person:

class\_uri:  __sdo:Person__

attributes:

family\_name:

slot\_uri:  __sdo:familyName__

address:

slot\_uri:  __sdo:address__

name: example\-OBO\-schema

classes:

Person:

class\_uri:  __NCBITaxon:9606__   <span style="color:#999999">\#\# Homo sapiens</span>

attributes:

surname:

slot\_uri:  __IAO:0000590__   <span style="color:#999999">\#\# written name</span>

home\_address:

slot\_uri:  __IAO:0000422__   <span style="color:#999999">\#\# postal address</span>

family\_name: Wu

address: 1 my street\, Oakville

surname: Wu

home\_address: 1 my street\, Oakville

# Level 1 Mapping: mediated by URI mapping

name: example\-semweb\-schema

classes:

Person:

class\_uri:  __sdo:Person__

attributes:

family\_name:

slot\_uri:  __sdo:familyName__

address:

slot\_uri:  __sdo:address__

name: example\-OBO\-schema

classes:

Person:

class\_uri:  __NCBITaxon:9606__   <span style="color:#999999">\#\# Homo sapiens</span>

attributes:

surname:

slot\_uri:  __IAO:0000590__   <span style="color:#999999">\#\# written name</span>

home\_address:

slot\_uri:  __IAO:0000422__   <span style="color:#999999">\#\# postal address</span>

| subject_id | object_id |
| :-: | :-: |
| sdo:Person | NCBITaxon:9606 |
| sdo:familyName | IAO:nnnn |
| sdo:address | IAO:0000422 |

family\_name: Wu

address: 1 my street\, Oakville

surname: Wu

home\_address: 1 my street\, Oakville

\[sdo:familyName “Wu”

sdo:address “1 my street\, Oakville”

\]

\[sdo:familyName “Wu”

sdo:address “1 my street\, Oakville”

\]

# Level 1: HOWTO

* Compose three commands:
* linkml\-convert \-s schema1\.yaml data1\.yaml \-o data1\.ttl
* sssom\-map\-iris \-i data1\.ttl \-m schema1\-to\-schema2\.sssom\.tsv \-o data2\.ttl
* linkml\-convert \-s schema2\.yaml data2\.ttl \-o data2\.yaml
* That’s it\!
* TODO:
* sssom\-map\-iris does not yet exist \(?\)\, but should be trivial
* Fold into wrapper CLI tool
* Nuances:
* Schemas have nuanced differences: not everything with be skos:exact
* We can distinguish 3 flavors of level 1 mapping:
  * Precise\, bidirectional: follow exact only
  * Valid\, unidirectional: follow exact \+ broad
  * Loose: any mapping

# Level 1 variant: mappings in schema

name: example\-semweb\-schema

classes:

Person:

class\_uri:  __sdo:Person__

__    __ exact\_mappings: \[“NCBITaxon:9606”\]

attributes:

family\_name:

slot\_uri:  __sdo:familyName__

__        exact\_mappings: \[“IAO:nnnn”\]__

address:

slot\_uri:  __sdo:address__

__        exact\_mappings: \[“IAO:0000422”\]__

name: example\-OBO\-schema

classes:

Person:

class\_uri:  __NCBITaxon:9606__   <span style="color:#999999">\#\# Homo sapiens</span>

attributes:

surname:

slot\_uri:  __IAO:0000590__   <span style="color:#999999">\#\# written name</span>

home\_address:

slot\_uri:  __IAO:0000422__   <span style="color:#999999">\#\# postal address</span>

family\_name: Wu

address: 1 my street\, Oakville

surname: Wu

home\_address: 1 my street\, Oakville

\[sdo:familyName “Wu”

sdo:address “1 my street\, Oakville”

\]

\[sdo:familyName “Wu”

sdo:address “1 my street\, Oakville”

\]

# Advantages of RDF as an intermediate

* Use of IRIs
* Separation of concerns
  * Structural differences \(e\.g\. inlining\) are already handled by linkml convert
  * Allows us to focus on semantic mappings

# Lessons learned so far: think about mappings

![](img/Mapping%20Between%20LinkML%20Schemas10.png)

![](img/Mapping%20Between%20LinkML%20Schemas11.png)

_[https://linkml\.io/linkml/faq/modeling\.html\#when\-is\-it\-important\-to\-have\-mappings](https://linkml.io/linkml/faq/modeling.html#when-is-it-important-to-have-mappings)_

_[https://github\.com/alliance\-genome/agr\_curation\_schema/blob/main/model/schema/agent\.yaml](https://github.com/alliance-genome/agr_curation_schema/blob/main/model/schema/agent.yaml)_

# More complex mappings: level 2 and above

* TODO: define levels 2 and above
* Examples of kinds of features:
  * merging/splitting fields; e\.g\. full\_name = first \+ “ “ \+ last
  * Unit conversion or baked\-in units to explicit units
  * Normalization/denormalization \(aka flattening\)
  * Complex logic
    * If conditions A\, B\, C and not D are met then copy field F from X to Y

# LinkML Rule and Inference Framework

* Current use case is  __intra\-schema__  inference
  * Easy to invoke on command line
  * Needs more docs\!
* Could form basis of  __inter\-schema__  DSL
* Examples
  * Schemas differ in units
  * Schemas differ in categorical vs quantitative

![](img/Mapping%20Between%20LinkML%20Schemas12.png)

Current use case is  __intra\-schema__  inference

Could form basis of  __inter\-schema__  DSL

![](img/Mapping%20Between%20LinkML%20Schemas13.png)

# Datalog

Datalog could serve as the powerful basis of an expressive declarative transformation language

![](img/Mapping%20Between%20LinkML%20Schemas14.png)

_[https://linkml\.io/linkml\-datalog](https://linkml.io/linkml-datalog)_

# Approach for level 2+

* Do we even want a generic mapping framework in LinkML here?
* This is a good “ __parasitization__  hook”
  * Do complex stuff using an existing framework
  * TBD: derive or semi\-derive mapping specification?
* This is also a code bespoke procedural code hook
  * Do the generic stuff with linkml\-convert and isomorphic IRI mapping
  * Do more complex stuff in code

# General approach for level 2+; same to same

name: example\-semweb\-schema

classes:

Person:

class\_uri:  __sdo:Person__

attributes:

family\_name:

slot\_uri:  __sdo:familyName__

address:

slot\_uri:  __sdo:address__

name: example\-OBO\-schema

classes:

Person:

class\_uri:  __NCBITaxon:9606__   <span style="color:#999999">\#\# Homo sapiens</span>

attributes:

surname:

slot\_uri:  __IAO:0000590__   <span style="color:#999999">\#\# written name</span>

home\_address:

slot\_uri:  __IAO:0000422__   <span style="color:#999999">\#\# postal address</span>

family\_name: Wu

address: 1 my street\, Oakville

surname: Wu

home\_address: 1 my street\, Oakville

JSON  _OR_  XML  _OR_  YAML  _OR_  RDF  _OR_  SQL

__JSON __  _OR_  __ XML __  _OR_  __ YAML __  _OR_  __ RDF __  _OR_  __ SQL__

__\(matches the one on the left\)__

__Existing __  __mapping__  __ framework \(X to X\)__

# Example of same-to-same: jsonpath-lifter

name: example\-semweb\-schema

classes:

Person:

class\_uri:  __sdo:Person__

attributes:

family\_name:

slot\_uri:  __sdo:familyName__

address:

slot\_uri:  __sdo:address__

name: example\-OBO\-schema

classes:

Person:

class\_uri:  __NCBITaxon:9606__   <span style="color:#999999">\#\# Homo sapiens</span>

attributes:

surname:

slot\_uri:  __IAO:0000590__   <span style="color:#999999">\#\# written name</span>

home\_address:

slot\_uri:  __IAO:0000422__   <span style="color:#999999">\#\# postal address</span>

family\_name: Wu

address: 1 my street\, Oakville

surname: Wu

home\_address: 1 my street\, Oakville

__Jsonpath\-lifter \(JSON to JSON\)__

# Example of same-to-same: awk

# Example of same-to-same: SQL

INSERT INTO Agent AS SELECT

Person\.last\_name AS Agent\.surname\,

CONCAT\(Person\.full\_name\, “ “\, Person\.first\) AS Agent\.full\_name\,

…

CONSTRUCT \{

\[

a schema:Person ;

my:fullName STRCAT\(\.\.\.\)

\]

\}

WHERE \{

?person a schema:Person ;

schema:firstName ;

schema:lastName ;

…

\}

__SPARQL CONSTRUCT__

__RDF__  __ Engine or Triplestore__

# Example of same-to-same: Python (LinkML objects)

def convert\(p: Person\) \-> Agent:

return Agent\(p\.id\,

full\_name=f”\{\.\.\} \{\.\.\}”\,

…

__Conversion script__

# General approach for level 2+; heteromorphic

name: example\-semweb\-schema

classes:

Person:

class\_uri:  __sdo:Person__

attributes:

family\_name:

slot\_uri:  __sdo:familyName__

address:

slot\_uri:  __sdo:address__

name: example\-OBO\-schema

classes:

Person:

class\_uri:  __NCBITaxon:9606__   <span style="color:#999999">\#\# Homo sapiens</span>

attributes:

surname:

slot\_uri:  __IAO:0000590__   <span style="color:#999999">\#\# written name</span>

home\_address:

slot\_uri:  __IAO:0000422__   <span style="color:#999999">\#\# postal address</span>

family\_name: Wu

address: 1 my street\, Oakville

surname: Wu

home\_address: 1 my street\, Oakville

_L_  _inkml\-convert_

_OPTIONAL_

_L_  _inkml\-convert_

_OPTIONAL_

JSON  _OR_  XML  _OR_  YAML  _OR_  RDF  _OR_  SQL

__JSON __  _OR_  __ XML __  _OR_  __ YAML __  _OR_  __ RDF __  _OR_  __ SQL__

__\(__  _different_  __ from the one on the left\)__

__Existing mapping framework \(X to Y\)__

# Example: YARRRML

name: example\-semweb\-schema

classes:

Person:

class\_uri:  __sdo:Person__

attributes:

family\_name:

slot\_uri:  __sdo:familyName__

address:

slot\_uri:  __sdo:address__

name: example\-OBO\-schema

classes:

Person:

class\_uri:  __NCBITaxon:9606__   <span style="color:#999999">\#\# Homo sapiens</span>

attributes:

surname:

slot\_uri:  __IAO:0000590__   <span style="color:#999999">\#\# written name</span>

home\_address:

slot\_uri:  __IAO:0000422__   <span style="color:#999999">\#\# postal address</span>

![](img/Mapping%20Between%20LinkML%20Schemas15.png)

family\_name: Wu

address: 1 my street\, Oakville

surname: Wu

home\_address: 1 my street\, Oakville

__YARRRML \(JSON/YAML to RDF\)__

# Example: YARRRML, native mappings

name: example\-semweb\-schema

classes:

Person:

class\_uri:  __sdo:Person__

attributes:

family\_name:

slot\_uri:  __sdo:familyName__

address:

slot\_uri:  __sdo:address__

name: example\-OBO\-schema

classes:

Person:

class\_uri:  __NCBITaxon:9606__   <span style="color:#999999">\#\# Homo sapiens</span>

attributes:

surname:

slot\_uri:  __IAO:0000590__   <span style="color:#999999">\#\# written name</span>

home\_address:

slot\_uri:  __IAO:0000422__   <span style="color:#999999">\#\# postal address</span>

family\_name: Wu

address: 1 my street\, Oakville

surname: Wu

home\_address: 1 my street\, Oakville

__mapping\.yarrrml\.yml__

# Example: YARRRML, compiled mappings

name: example\-semweb\-schema

classes:

Person:

class\_uri:  __sdo:Person__

attributes:

family\_name:

slot\_uri:  __sdo:familyName__

address:

slot\_uri:  __sdo:address__

Mappings __:__

__   … \< TO BE DEFINED LINKML MAPPING SPEC >__

name: example\-OBO\-schema

classes:

Person:

class\_uri:  __NCBITaxon:9606__   <span style="color:#999999">\#\# Homo sapiens</span>

attributes:

surname:

slot\_uri:  __IAO:0000590__   <span style="color:#999999">\#\# written name</span>

home\_address:

slot\_uri:  __IAO:0000422__   <span style="color:#999999">\#\# postal address</span>

family\_name: Wu

address: 1 my street\, Oakville

surname: Wu

home\_address: 1 my street\, Oakville

__mapping\.yarrrml\.yml__

# Hyperparasitism is good

name: example\-semweb\-schema

classes:

Person:

class\_uri:  __sdo:Person__

attributes:

family\_name:

slot\_uri:  __sdo:familyName__

address:

slot\_uri:  __sdo:address__

Mappings __:__

__   … \< TO BE DEFINED LINKML MAPPING SPEC >__

name: example\-OBO\-schema

classes:

Person:

class\_uri:  __NCBITaxon:9606__   <span style="color:#999999">\#\# Homo sapiens</span>

attributes:

surname:

slot\_uri:  __IAO:0000590__   <span style="color:#999999">\#\# written name</span>

home\_address:

slot\_uri:  __IAO:0000422__   <span style="color:#999999">\#\# postal address</span>

__mapping\.yarrrml\.yml__

family\_name: Wu

address: 1 my street\, Oakville

surname: Wu

home\_address: 1 my street\, Oakville

# Alternative: Direct translation language

* Desiderata
* Ability to compile to scalable frameworks
  * E\.g\. compile to SQL
* Simple for simple tasks
* Layer on existing expression language
  * Provides path to safe subset of host language \(Python\)
  * Can be easily implemented in other languages

![](img/Mapping%20Between%20LinkML%20Schemas16.png)

![](img/Mapping%20Between%20LinkML%20Schemas17.png)

# Normalized to Denormalized (modeling SSSOM)

SQL INSERT \(or CREATE VIEW\)

![](img/Mapping%20Between%20LinkML%20Schemas18.png)

SQL FROM Clause

\(implicit INNER JOIN/WHERE\)

SQL SELECT … AS clause

# Relationship to profiles TODO

Profiles/IGs can be seen as a sub\-case of schema mapping

# Current progress

_[https://github\.com/linkml/linkml/issues/533](https://github.com/linkml/linkml/issues/533)_  map to YARRRML

Vincent Vemonet has started on linkml\->rml

_[https://github\.com/vemonet/linkml/blob/add\-gen\-rml/linkml/generators/rmlgen\.py](https://github.com/vemonet/linkml/blob/add-gen-rml/linkml/generators/rmlgen.py)_

# Relationship to Koza

# Koza ingests often require multiple files

![](img/Mapping%20Between%20LinkML%20Schemas19.png)

![](img/Mapping%20Between%20LinkML%20Schemas20.png)

# See Also

Revisiting BioWeave \(Kent Shefchek\, 2020?\)

_[https://docs\.google\.com/presentation/d/1DYiWXoz3iHM2PvMFD0hRpJ544tnHawg00PBwNuESo44/edit\#slide=id\.gb33d7ddd1b\_0\_93](https://docs.google.com/presentation/d/1DYiWXoz3iHM2PvMFD0hRpJ544tnHawg00PBwNuESo44/edit#slide=id.gb33d7ddd1b_0_93)_

# Automating mapping

* Should we pursue approaches to automate mapping?
  * Some of the functionality is already in schema\-automator\. E\.g\. auto\-annotating schema elements using ontologies
* Isomorphic schema mapping discovery analogous to ontology mapping
  * Can a boomer type approach help?
    * E\.g\. given multiple loose mappings with alternative interpretations\, which ones give coherent results
* Other approaches
  * Inductive Logic Programming: transformations as logic programs
  * Genetic programming: transformations as lambda functions
  * Deep Learning: e\.g\. Language Models for translation
* There is already a rich literature spanning decades here to be parasitized…

# Summary: just tell me what to do today

* For isomorphic mappings:
  * Stay within LinkML/SSSOM
  * No need for custom code\, it all works
* For complex mappings:
  * It depends\!
  * Do the structural mapping with linkml\-convert
  * Implement the complex logic as you see fit\, depending on multiple factors\. Any of the following may be valid
    * Koza
    * Awk
    * SPARQL CONSTRUCTS or SELECTS
    * Custom python
    * YARRRML
    * SQL INSERTs
    * XSLT
    * Jsonpath\-lifter
    * …\.

# Roadmap

* 2022: Continue to gather use cases\, experiment
* 2023: If funding permits
  * Extend metamodel to include complex mapping
  * Implement EITHER
    * Parasitizing converters
    * Direct mapping framework
  * TBD: Is this Koza2?

