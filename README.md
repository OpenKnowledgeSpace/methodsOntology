# methodsOntology
Repository for development of the neuroscience methods ontology.

## Files
ns_methods.obo will hold the methods concepts
ns_entities.obo will hold entities that are subjects/specimines or tools/reagents
ns_datatypes will hold datatypes that are the outputs of methods

## Basic design principles
The objective of this ontology is to provide a lightweight framework for annotating
scientific protocols. To that end our initial approach is to separate the entities
and the data that are the inputs and outputs of protocols, from the higher level
methods concepts that describe those protocols.

The basic structure for each obo file will be a single parrent is_a hierarchy.
Other limited modeling may be added later as needed in order to serve other systems
that will directly represent protocols themselves.

## Contributing
If you would like to contribute changes please fork the repository and submit pull requests. Thanks!

