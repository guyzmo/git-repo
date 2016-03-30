#!/usr/bin/env python

import os

import betamax
from betamax_serializers import pretty_json

record_mode = 'never' if os.environ.get('TRAVIS_GH3') else 'once'

# create default bogus values for tokens and namespaces if missing for pytest
# to run without environment values
# also if an environment variable is not set, then we don't want to record cassettes
for service_name in ('github', 'gitlab', 'bitbucket'):
    token_name = 'PRIVATE_KEY_{}'.format(service_name.upper())
    namespace_name = '{}_NAMESPACE'.format(service_name.upper())
    if token_name not in os.environ:
        os.environ[token_name] = 'not_configured:test' # using a : for bitbucket's case
        record_mode = 'never'
    if namespace_name not in os.environ:
        os.environ[namespace_name] = 'not_configured'
        record_mode = 'never'

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



