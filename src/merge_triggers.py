#!/usr/bin/env python3
"""
    This file should be called automatically whenever a pull request
    is merge with the reference ontologies. It does two things.
    1) removes temporary terms from the suggestion server
       that have been added by said pull request
    2) removes temporary synonyms from the suggestion server
       that have been added by said pull request

    NOTE: since there will only be one version of the suggestion server
    tests builds from the pull requesting fork (and thus ALL builds) will
    need to gracefully handle cases where suggested terms have already
    been added to the ttl.

    NOTE: Deployment of the ontologies shall not ever modify the suggestion
    server, only curatorial workflows will remove terms. Namely THIS FILE.
    Since make_ttl.py will be robust to dumplicate suggested synonyms we
    do not have to worry about locking and race conditions between builds
    and using a database provides additional transaction safety (not that
    we really need it).
"""

