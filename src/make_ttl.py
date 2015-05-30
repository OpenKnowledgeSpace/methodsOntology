#!/usr/bin/env python3
"""
    Make the ttl files to load into scigraph from 3 sources:
    1) reference ttl files that contain the full list of classes with defs
    2) the suggested terms and synonyms database
    3) synonyms sourced from the synonym ontology

    These sources are compiled into a set of ttl files that will then
    be loaded into scigraph. For development the build system should
    allow granular control over exactly which sources are used for a
    given build so bad performance can be isolated to specific sources.
"""

# TODO find out if it is possible to update the neo4j graph via
# owlapi without having to reload the whole ontology stopping services

# list of sources to draw from

# start with each ttl file in methodsOntology/ttl (base ttl)
# go to the synonym store
    # for each ID in the store pull out only the term
    # map that term to synonym, acronym, or abbreviation
    # append those synonyms to the relevant entry in the base ttl
    # we probably also need a model that has a flag to prevent
    # synonym loading for performance reasons
# go to the suggestion database terms
    # compile new terms into their own ttl file that has a TEMP curie
    # that curie can be used by the UI guys to toggle suggested terms
# go to the suggestion database synonyms
    # for each ID in the suggestion database
        #IF the synonym is not already listed (must handle test builds)
            # append suggested synonyms under 'TEMPsynonym' annotationPropery
        #ELSE
            # show an error that the synonym is already in the ttl
            # useful for validating correct additions (E{num errors})
            # and debugging production issues with curation race conds
    # might also want to append under 'synonym' for the time being
    # we will eventually implement the ability to have TEMP come out
    # of the scigraph services but we don't have that right now

# construct version information from the base ttl hash and/or the syn hash
    # ignore version information from the temp syn hash
# the full ttl files are now done and ready to load into scigraph.
