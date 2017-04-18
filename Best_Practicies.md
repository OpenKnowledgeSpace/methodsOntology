# Introduction 
This document gather best practices for lightweight ontology design and edition. It should be considered as a guide when contributing to nexus ontologies.


## Best practices on lightweight domain ontologies 

### Concept naming

#### Concept as single nouns

* Use short name
* Use five letter prefix name and no underscore
* Use camel case notation
* In case of lighweight vocabulary use words rather than numbers as fragment (ex. HBP_ACT:activity instead of HBP_ACT:0000001)

### Concept Annotations: Minimal fields
 
 * rdf:label
 * rdf:prefLabel
 * definition
 
 #### Properties as verb senses
 
 #### Use fo meaningful prefixes or suffixes to relate properties and classes
 
 ### Use of authorative vocabulary

authorative vocabulary list:
 * skos: 

#### Dereferenceability 


### Frequent errors

* Don't use rdfs:isDefinedBy to add a definition annotation to an ontology entity (concept, property

#### False friends
* rdfs:isDefinedBy is not for providing a textual definition for a concept or a property but for indicating a resource within which the concept or the property is defined.
