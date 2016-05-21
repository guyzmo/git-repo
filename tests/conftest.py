#!/usr/bin/env python

import os

import betamax
from betamax_serializers import pretty_json

record_mode = 'once'

if os.environ.get('TRAVIS_GH3'):
    # create default bogus values for tokens and namespaces if missing for pytest
    # to run without environment values
    # also if an environment variable is not set, then we don't want to record cassettes
    record_mode = 'never'
    for service_name in ('github', 'gitlab', 'bitbucket'):
        token_name = 'PRIVATE_KEY_{}'.format(service_name.upper())
        namespace_name = '{}_NAMESPACE'.format(service_name.upper())
        if token_name not in os.environ:
            os.environ[token_name] = 'not_configured:test' # using a : for bitbucket's case
        if namespace_name not in os.environ:
            os.environ[namespace_name] = 'not_configured'
else:
    import git, getpass
    config = git.config.GitConfigParser(os.path.join(os.environ['HOME'], '.gitconfig'))
    conf_section = list(filter(lambda n: 'gitrepo' in n, config.sections()))
    key_dict = {section.split('"')[1] :config.get_value(section, 'privatekey') for section in conf_section}
    for service, key in key_dict.items():
        token_name = 'PRIVATE_KEY_{}'.format(service.upper())
        namespace_name = '{}_NAMESPACE'.format(service.upper())
        os.environ[token_name] = key
        os.environ[namespace_name] = os.environ.get('GITREPO_NAMESPACE', getpass.getuser())

api_token_github = os.environ['PRIVATE_KEY_GITHUB']
api_token_gitlab = os.environ['PRIVATE_KEY_GITLAB']
api_token_bitbucket = os.environ['PRIVATE_KEY_BITBUCKET']

github_namespace = os.environ['GITHUB_NAMESPACE']
gitlab_namespace = os.environ['GITLAB_NAMESPACE']
bitbucket_namespace = os.environ['BITBUCKET_NAMESPACE']

betamax.Betamax.register_serializer(pretty_json.PrettyJSONSerializer)

with betamax.Betamax.configure() as config:
    config.default_cassette_options['record_mode'] = record_mode
    config.cassette_library_dir = 'tests/integration/cassettes'
    config.default_cassette_options['serialize_with'] = 'prettyjson'
    config.define_cassette_placeholder('<PRIVATE_KEY_GITHUB>', api_token_github)
    config.define_cassette_placeholder('<PRIVATE_KEY_GITLAB>', api_token_gitlab)
    config.define_cassette_placeholder('<PRIVATE_KEY_BITBUCKET>', api_token_bitbucket)
    config.define_cassette_placeholder('<GITHUB_NAMESPACE>', github_namespace)
    config.define_cassette_placeholder('<GITLAB_NAMESPACE>', gitlab_namespace)
    config.define_cassette_placeholder('<BITBUCKET_NAMESPACE>', bitbucket_namespace)



