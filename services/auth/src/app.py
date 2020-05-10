"""
Auth server.
Provides endpoints:
    * obtain access token;
    * check authorization (validate access token);
"""


from flask import Flask, request, jsonify
from jose import jwt
import json
import logging
import os
import requests
from typing import Text


LOGLEVEL = os.getenv('LOGLEVEL', 'INFO').upper()
logging.basicConfig(level=LOGLEVEL)

AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
AUTH0_API_IDENTIFIER = os.getenv('AUTH0_API_IDENTIFIER')
ALGORITHMS = ['RS256']

app = Flask(__name__)


class JWKSCache:

    JWKS_CACHED_JSON = '/tmp/jwks.json'

    def __init__(self, auth0_domain):
        self.auth0_domain = auth0_domain

    def get_jwks(self):

        self.refresh_jwks_json()

        with open(self.JWKS_CACHED_JSON, 'r') as jwks_json_file:
            return json.load(fp=jwks_json_file)

    def refresh_jwks_json(self):

        # TODO (Alex): add JWKS json structure validation
        # TODO (Alex): handle error when specified auth0_domain not found
        if not os.path.exists(self.JWKS_CACHED_JSON):

            jwks_resp = requests.get(
                'https://' + self.auth0_domain + '/.well-known/jwks.json'
            )
            jwks = jwks_resp.json()

            with open(self.JWKS_CACHED_JSON, 'w') as jwks_json_file:
                json.dump(obj=jwks, fp=jwks_json_file)


class AuthError(Exception):
    """Format error response and append status code."""

    def __init__(self, error, status_code):

        self.error = error
        self.status_code = status_code


JWKS_CACHE = JWKSCache(auth0_domain=AUTH0_DOMAIN)


@app.errorhandler(AuthError)
def handle_auth_error(ex: AuthError):

    logging.debug(f'error handling: {str(ex)}')

    response = jsonify(ex.error)
    response.status_code = ex.status_code

    return response


def get_token_auth_header():
    """Obtains the access token from the Authorization Header"""

    logging.debug('obtain token from header')

    auth = request.headers.get('Authorization', None)

    if not auth:

        logging.debug('authorization header missing')

        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected'
        }, 401)

    parts = auth.split()

    if parts[0].lower() != 'bearer':

        logging.debug('invalid header: authorization header must start with bearer')

        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with Bearer'
        }, 401)

    elif len(parts) == 1:

        logging.debug('invalid header: token not found')

        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found'
        }, 401)

    elif len(parts) > 2:

        logging.debug('invalid header: authorization header must be Bearer token')

        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be Bearer token'
        }, 401)

    token = parts[1]

    return token


def check_auth(access_token: Text):
    """Check authorization - validate access_token"""

    logging.info('check authorization')

    jwks = JWKS_CACHE.get_jwks()

    try:

        unverified_header = jwt.get_unverified_header(access_token)

    except jwt.JWTError:

        logging.debug('invalid_header: use an rs256 signed jwt access token')

        raise AuthError({
            'code': 'invalid_header',
            'description': 'Invalid header. Use an RS256 signed JWT Access Token'
        }, 401)

    if unverified_header['alg'] == 'HS256':

        logging.debug('invalid_header: use an rs256 signed jwt access token')

        raise AuthError({
            'code': 'invalid_header',
            'description': 'Invalid header. Use an RS256 signed JWT Access Token'
        }, 401)

    rsa_key = {}

    for key in jwks.get('keys', []):

        if key['kid'] == unverified_header['kid']:

            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    if rsa_key:
        try:

            jwt.decode(
                access_token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=AUTH0_API_IDENTIFIER,
                issuer='https://'+AUTH0_DOMAIN+'/'
            )

        except jwt.ExpiredSignatureError:

            logging.debug('token expired')

            JWKS_CACHE.refresh_jwks_json()

            raise AuthError({
                'code': 'token_expired',
                'description': 'token is expired'
            }, 401)

        except jwt.JWTClaimsError:

            logging.debug('incorrect claims, please check the audience and issuer')

            raise AuthError({
                'code': 'invalid_claims',
                'description': 'incorrect claims, please check the audience and issuer'
            }, 401)

        except Exception as e:
            logging.error(e, exc_info=True)
            logging.debug('invalid_header: unable to parse authentication token')

            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token'
            }, 401)

        return

    logging.debug('invalid_header: to find appropriate key')

    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find appropriate key'
    }, 401)


@app.route('/token', methods=['POST'])
def token():
    """Get access token"""

    logging.debug('get access token')

    headers = {'content-type': 'application/json'}
    payload = {
        'client_id': request.form.get('client_id'),
        'client_secret': request.form.get('client_secret'),
        'audience': AUTH0_API_IDENTIFIER,
        'grant_type':'client_credentials'
    }
    resp = requests.post(
        url=f'https://{AUTH0_DOMAIN}/oauth/token',
        json=payload,
        headers=headers
    )
    data = resp.json()

    if 'access_token' not in data:

        logging.debug('auth0 response does not contain access token')

        raise AuthError({
            'code': data.get('error', ''),
            'description': data.get('error_description', ''),
        }, resp.status_code)

    access_token = data['access_token']

    return {'access_token': access_token}


@app.route('/token/validate')
def validate_token():
    """Validate (confirm) access token"""

    logging.debug('validate token')
    token = get_token_auth_header()
    check_auth(token)

    return ''


if __name__ == '__main__':

    app.run(host='0.0.0.0', port=1234, debug=True)
