# linkml-map 

Datamodel for LinkML schema mappings and transformations.

A mapper generates instances of a *target* data model from
instances of a *source* data model. This transformation process
is guided by a *TransformationSpecification*.

The specification is independent of any one method for transforming
data. It allows different approaches, including:

- direct implementation, transforming python or json objects
- translation of the specification into SQL commands, to operate on relations
- translation of the specification into SPARQL CONSTRUCTs, to operate on triples
- translation into another specification language, such as R2RML

URI: https://w3id.org/linkml/transformer