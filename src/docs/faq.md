# FAQ

## Why another framework?

There are a number of excellent frameworks for performing mapping and data transformations.
The LinkML Transformer framework was born out of a need for a framework that:

- was not inherently tied to:
     - a particular serialization format (e.g. RDF, JSON, ...)
     - a particular programming language (e.g. Python, Java, ...)
     - a particular database system or database language (e.g. PostgreSQL or SQL or SPARQL)
     - not tied to a particular kind of transformation (e.g. ORM or Tables to RDF)
- was a natural fit for the LinkML data modeling framework
- was declarative and easy to perform machine reasoning over
- is simple for simple use cases

In its current state, this framework is less powerful and expressive than many other frameworks
or methodologies for performing transformations. If you need to perform complex data transformations,
you might be better off using an expressive query language like SPARQL or SQL, or even just coding
transformations directly in a programming language or library like Python or Pandas (but note that
even for the coding use case, the LinkML Transformer framework can be useful as a standard way
of *documenting* transformations).

Currently the main use case for this framework is *mostly isomorphic* transformations, with lightweight
manipulations. These lend themselves well to a declarative framework. Uses cases that are a particularly good fit
involve mapping between data-dictionary like standards, with large numbers of metadata elements, where these
elements can often be mapped one-to-one, or with simple manipulations (e.g. unit conversions).

The origins lie partly in the SSSOM standard, which is intended as an ultra-simple way of specifying
precise mappings between *entities* (e.g. schema.org Person is the same as DBPedia person). We observed
that many people wanted to extend the language to perform more complex mappings. To address this, we
help a workshop at the Biocuration conference in Padua, Italy in 2022.

- [Discussion](https://github.com/orgs/linkml/discussions/1829)
- [SSSOM paper](https://academic.oup.com/database/article/doi/10.1093/database/baac035/6591806)
- [SSSOM Update 2023](https://ceur-ws.org/Vol-3591/om2023_STpaper3.pdf)
- [SSSOM Complex Mappings Workshop 2023](https://www.youtube.com/playlist?list=PLqu_J7ADQtKyX55F7RqZtaSS7TwGd3MoR)
- [Mapping Data Structures: Challenges and Approaches](https://doi.org/10.5281/zenodo.10343505)
