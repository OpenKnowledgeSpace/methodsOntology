# methodsOntology
Repository for development of the neuroscience methods ontology.

## Files
### source-materials/
Source files that are inputs for generating the ttl files.

### src/
The code that generates the ttl.

### ttl/
Ontology outputs to be loaded into scigraph.
nsupper.ttl holds an absurdly lightweight upper ontology
nsmethods.ttl will hold the methods concepts
nsbeing.ttl will hold entities that are subjects/specimines or tools/reagents
nsdatatypes.ttl will hold datatypes that are the outputs of methods

### scigraph/
Scigraph configuration yaml files.

## Basic design principles
The objective of this ontology is to provide a lightweight framework for annotating
scientific protocols. To that end our initial approach is to separate the entities
and the data that are the inputs and outputs of protocols, from the higher level
methods concepts that describe those protocols.

The basic structure for each obo file will be a single parrent is_a hierarchy.
Other limited modeling may be added later as needed in order to serve other systems
that will directly represent protocols themselves.

## License
Code is licensed under the MIT license and ontologies are licensed under CC3.0. Source materials
are licensed under CC3.0 or their existing license.

## Contributing
If you would like to contribute changes please fork the repository and submit pull requests. Thanks!

