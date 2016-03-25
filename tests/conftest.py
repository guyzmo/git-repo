#!/usr/bin/env python

import betamax
from betamax_serializers import pretty_json

# tests/conftest.py
import os

api_token_github = os.environ.get('PRIVATE_KEY_GITHUB', 'not_configured')
api_token_gitlab = os.environ.get('PRIVATE_KEY_GITLAB', 'not_configured')
api_token_bitbucket = os.environ.get('PRIVATE_KEY_BITBUCKET', 'not_configured')

betamax.Betamax.register_serializer(pretty_json.PrettyJSONSerializer)

with betamax.Betamax.configure() as config:
    config.cassette_library_dir = 'tests/integration/cassettes'
    config.default_cassette_options['serialize_with'] = 'prettyjson'
    config.define_cassette_placeholder('<PRIVATE_KEY_GITHUB>', api_token_github)
    config.define_cassette_placeholder('<PRIVATE_KEY_GITLAB>', api_token_gitlab)
    config.define_cassette_placeholder('<PRIVATE_KEY_BITBUCKET>', api_token_bitbucket)



