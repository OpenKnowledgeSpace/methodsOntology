# Introduction 
This document gathers best practices for lightweight domain ontology design and edition. 
It should be considered as a collection of guidelines to follow when contributing to nexus ontologies. 

## Namespaces
The following table shows the set of prefix names and their corresponding namespaces used this document.
....


## Best practices on lightweight domain ontology edition


### Ontology documentation best practices

#### Topic and provenance
An ontology should be annotated with its purpose as well as its provenance (we care about provenance right!).  The authorative vocabulary for doing this is the dublin core vocabulary.
Its official prefix name is **dc** and the corresponding namespace is **<http://purl.org/dc/elements/1.1/>**.
The following annotation should be provided: 
* dc:title
* dc:creator
* dc:contributor
* dc:subject
 
#### Versioning

 owl:version
 
 ....

### Ontology entity naming

An ontology as well as an ontology entity has a [URI](https://www.w3.org/TR/uri-clarification) as identif       ier. For example "http://purl.obolibrary.org/obo/NCBITaxon_10090" is the URI of a "Mus musculus" concept. 
The previous URI can have a short form which is called prefix (a stable string) for the ontology and [CURIE](https://www.w3.org/TR/curie) for the ontology entities. 
Let take again the previous example. The prefix name of (the short form of) "http://purl.obolibrary.org/obo/NCBITaxon_10090" can be "obo" and the curie of the concept "obo:NCBITaxon_10090". 
Given the curie "obo:NCBITaxon_10090", "obo" is the prefix name and "NCBITaxon_10090" the fragment.

How to write a good CURIE:

 - Use a five letter prefix name and no underscore (for example **activ**:0000001 instead of **HBP_ACT**:0000001). 
 - A lowercase prefix name should be preferred: "activ" instead of "ACTIV"
 - Use words rather than numbers as fragment (ex. **activ:activity** instead of **activ:0000001**)

...

#### Concept name as single noun
A concept name refers to its curie's fragment. 

- Use [camel case](https://en.wikipedia.org/wiki/Camel_case) notation:
    * concept name should start with a capital letter
    * no space is allowed
    * Good example **"damo:ChannelDistribution"**
    * Bad examples  **"damo:channelDistribution"** or **"damo:channel_Distribution"**


#### Concept Annotations: minimal fields
 
Here are some annotation properties that can be attached to a concept to describe it.
 
 * rdfs:label: a short label that can be used to name the concept. At least a label in english should be provided (using @en as language tag).
               Note that only one label per language is allowed.
 
 * skos:prefLabel: a preferred label for a concept. The rdfs:label value can be reused here. Note that a skos:prefLabel is a rdfs:label.
 * skos:definition: used to provide a human readable definition of a concept.
 
 #### How to express synonyms

There are different ways of expressing synonyms in an ontology.
 
 Synonym scope:
 * Exact
 * broad
 ...

 
 #### Property name as verb sense
 
A property name refers to its curie's fragment. 
 
- Use verb as property name so that a triple (instance property instance) can be easily read.
    * for example: "file:aSpecificFile **prop:hasFileExtension** ext:csv" instead of "file:aSpecificFile **prop:fileExtension** ext:csv"
- Use mixed case notation:
    * property name should start with lower case and be capitalized thereafter
    * no space is allowed
    * Good example **"prop:hasFileExtension"**
    * Bad example  **"HBP_PROP:has_file_extension"** 
...

 
 #### Use fo meaningful prefixes or suffixes to relate properties and classes
 ...
 
 #### multi-lingual capabilities
  
  ...


#### Dereferenceability 


 
 ### Ontology Structure
  
  * Assign domain and ranges
  * 


 ### Use of authorative vocabulary
 
 Authorative vocabulary list:
 
  * skos: http://www.w3.org/2004/02/skos/core#
  * dc:	http://purl.org/dc/elements/1.1/
  
### Frequent errors

 * rdfs:isDefinedBy is not for providing a textual definition for a concept or a property but for indicating a resource within which the concept or the property is defined.
