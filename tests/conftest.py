#!/usr/bin/env python

import os

import betamax
from betamax_serializers import pretty_json

record_mode = 'once'

from git_repo.services.service import RepositoryService
services = list(RepositoryService.service_map.keys())

if os.environ.get('TRAVIS_GH3'):
    # create default bogus values for tokens and namespaces if missing for pytest
    # to run without environment values
    # also if an environment variable is not set, then we don't want to record cassettes
    record_mode = 'never'
    for service in services:
        token_name = 'PRIVATE_KEY_{}'.format(service.upper())
        namespace_name = '{}_NAMESPACE'.format(service.upper())
        if token_name not in os.environ:
            os.environ[token_name] = '_namespace_{}_:_private_'.format(service) # using a : for bitbucket's case
        if namespace_name not in os.environ:
            os.environ[namespace_name] = '_namespace_{}_'.format(service)
else:
    # if running tests "locally" and not in travis, let's try to extract the keys from
    # the local configuration if there is some local configuration. And exposes them as
    # environment variables.
    import git, getpass
    config = git.config.GitConfigParser(os.path.join(os.environ['HOME'], '.gitconfig'))

    # handle the different forms of token configuration item (yup, technical debt bites here)
    get_section = lambda s: 'gitrepo "{}"'.format(s)
    get_token = lambda s: config.get_value(get_section(s), 'token',
                            config.get_value(get_section(s), 'private_token',
                                config.get_value(get_section(s), 'privatekey',
                                        '_namespace_{}_:_private_'.format(s) # using a : for bitbucket's case
                                    )))
    # XXX temporary fix that should not be necessary when refactoring with pybitbucket
    get_default_namespace = lambda s: os.environ[token_name].split(':')[0] if s == 'bitbucket' else '_namespace_{}_'.format(s)

    for service in services:
        token_name = 'PRIVATE_KEY_{}'.format(service.upper())
        namespace_name = '{}_NAMESPACE'.format(service.upper())
        if token_name not in os.environ:
            os.environ[token_name] = get_token(service)
        if namespace_name not in os.environ:
            os.environ[namespace_name] = os.environ.get('GITREPO_NAMESPACE', get_default_namespace(service))

betamax.Betamax.register_serializer(pretty_json.PrettyJSONSerializer)

with betamax.Betamax.configure() as config:
    config.default_cassette_options['record_mode'] = record_mode
    config.cassette_library_dir = 'tests/integration/cassettes'
    config.default_cassette_options['serialize_with'] = 'prettyjson'
    # generating placeholders in betamax configuration for each service's key and default namespace
    for service in services:
        config.define_cassette_placeholder('<PRIVATE_KEY_{}>'.format(service.upper()), os.environ.get('PRIVATE_KEY_{}'.format(service.upper())))
        config.define_cassette_placeholder('<{}_NAMESPACE>'.format(service.upper()), os.environ.get('{}_NAMESPACE'.format(service.upper())))

