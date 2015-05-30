#!/usr/bin/env python3
"""
    Code for compiling the seed ttl ontologies from varous existing sources.
    This process will be replaced once the initial seed files are created.
    Those files will then act as the 'definitive' version to which all
    curated additions will be added and all edits will be made.
"""
from obo_io import OboFile

#paths
TTL_SRC = '../source-material/'

#supart prefixes
prefixes = [
    'header',
    'props',
    'classes',
]

#ontologies
onts = [
    'nsupper.ttl',
    'nsbeing.ttl',
    'nsmethods.ttl',
    'nsdatatypes.ttl',
]

# obo files
{
    'nsbeing.ttl':['ns_entities.obo'],
    'nsmethods.ttl':['ns_methods.obo'],
}
