#!/usr/bin/env python3
"""
NHS API JWT Authentication Script

This script automates the JWT authentication process for NHS application-restricted APIs.
It handles key generation, JWT signing, token retrieval, and API calls.

Manual steps still required:
1. Register your application on the API platform to get your App ID and API Key
2. Upload your public key (JWKS) to the developer portal OR host it yourself
"""

import json
import uuid
import base64
import argparse
from time import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

try:
    import jwt
    import requests
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
except ImportError as e:
    print("Missing required dependencies. Install with:")
    print("pip install PyJWT[crypto] requests cryptography")
    exit(1)


class NHSAPIAuth:
    """Handles NHS API authentication using JWT"""

    ENVIRONMENTS = {
        'dev': 'https://dev.api.service.nhs.uk/oauth2',
        'int': 'https://int.api.service.nhs.uk/oauth2',
        'prod': 'https://api.service.nhs.uk/oauth2'
    }

    def __init__(self, api_key: str, environment: str = 'int', kid: Optional[str] = None):
        """
        Initialize NHS API authentication handler

        Args:
            api_key: Your API key from the developer portal
            environment: Environment to use (dev, int, prod)
            kid: Key identifier (defaults to {environment}-1)
        """
        self.api_key = api_key
        self.environment = environment
        self.kid = kid or f"{environment}-1"
        self.base_url = self.ENVIRONMENTS.get(environment)

        if not self.base_url:
            raise ValueError(f"Invalid environment: {environment}. Must be one of {list(self.ENVIRONMENTS.keys())}")

        self.token_endpoint = f"{self.base_url}/token"
        self.access_token = None
        self.token_expiry = None

    def generate_key_pair(self, output_dir: str = ".") -> Tuple[str, str]:
        """
        Generate a 4096-bit RSA key pair

        Args:
            output_dir: Directory to save the keys

        Returns:
            Tuple of (private_key_path, public_key_path)
        """
        print(f"Generating 4096-bit RSA key pair with KID: {self.kid}")

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )

        # Save private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        private_key_path = Path(output_dir) / f"{self.kid}.pem"
        private_key_path.write_bytes(private_pem)
        print(f"✓ Private key saved to: {private_key_path}")

        # Save public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        public_key_path = Path(output_dir) / f"{self.kid}.pem.pub"
        public_key_path.write_bytes(public_pem)
        print(f"✓ Public key saved to: {public_key_path}")

        return str(private_key_path), str(public_key_path)

    def generate_jwks(self, public_key_path: str, output_path: Optional[str] = None) -> Dict:
        """
        Generate JWKS (JSON Web Key Set) from public key

        Args:
            public_key_path: Path to the public key PEM file
            output_path: Optional path to save JWKS JSON file

        Returns:
            JWKS dictionary
        """
        print(f"Generating JWKS from public key: {public_key_path}")

        # Load public key
        with open(public_key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())

        # Extract modulus
        public_numbers = public_key.public_numbers()
        n = public_numbers.n
        e = public_numbers.e

        # Convert to base64url format (without padding)
        n_bytes = n.to_bytes((n.bit_length() + 7) // 8, byteorder='big')
        n_b64 = base64.urlsafe_b64encode(n_bytes).decode('utf-8').rstrip('=')

        e_bytes = e.to_bytes((e.bit_length() + 7) // 8, byteorder='big')
        e_b64 = base64.urlsafe_b64encode(e_bytes).decode('utf-8').rstrip('=')

        # Create JWKS
        jwks = {
            "keys": [{
                "kty": "RSA",
                "n": n_b64,
                "e": e_b64,
                "alg": "RS512",
                "kid": self.kid,
                "use": "sig"
            }]
        }

        # Save JWKS if output path provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(jwks, f, indent=2)
            print(f"✓ JWKS saved to: {output_path}")

        print("✓ JWKS generated successfully")
        return jwks

    def generate_jwt(self, private_key_path: str, expires_in_minutes: int = 5) -> str:
        """
        Generate and sign a JWT

        Args:
            private_key_path: Path to the private key PEM file
            expires_in_minutes: JWT expiry time (max 5 minutes)

        Returns:
            Signed JWT string
        """
        if expires_in_minutes > 5:
            raise ValueError("JWT expiry must not exceed 5 minutes")

        # Load private key
        with open(private_key_path, 'r') as f:
            private_key = f.read()

        # Create claims
        # Use slightly less than requested time to account for clock skew
        # Subtract 10 seconds as a safety buffer
        current_time = int(time())
        expiry_seconds = (expires_in_minutes * 60) - 10

        claims = {
            "sub": self.api_key,
            "iss": self.api_key,
            "jti": str(uuid.uuid4()),
            "aud": self.token_endpoint,
            "exp": current_time + expiry_seconds
        }

        # Create additional headers
        additional_headers = {"kid": self.kid}

        # Sign JWT
        signed_jwt = jwt.encode(
            claims,
            private_key,
            algorithm="RS512",
            headers=additional_headers
        )

        # Debug info
        exp_datetime = datetime.fromtimestamp(claims['exp'])
        print(f"✓ JWT generated (expires at {exp_datetime})")
        print(f"  Current time: {datetime.fromtimestamp(current_time)}")
        print(f"  Expiry time:  {exp_datetime}")
        print(f"  Time until expiry: {(claims['exp'] - current_time)} seconds")

        return signed_jwt

    def get_access_token(self, private_key_path: str, force_refresh: bool = False) -> str:
        """
        Get an access token from the OAuth2 token endpoint

        Args:
            private_key_path: Path to the private key PEM file
            force_refresh: Force getting a new token even if current one is valid

        Returns:
            Access token string
        """
        # Check if we have a valid cached token
        if not force_refresh and self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                print("✓ Using cached access token")
                return self.access_token

        print("Requesting new access token...")

        # Generate JWT
        signed_jwt = self.generate_jwt(private_key_path)

        # Prepare request
        data = {
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": signed_jwt
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Make request
        try:
            response = requests.post(self.token_endpoint, data=data, headers=headers)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data['access_token']
            expires_in = int(token_data['expires_in'])

            # Cache expiry time (with 30 second buffer)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 30)

            print(f"✓ Access token obtained (expires in {expires_in} seconds)")
            return self.access_token

        except requests.exceptions.HTTPError as e:
            print(f"✗ Error getting access token: {e}")
            if e.response is not None:
                print(f"Response: {e.response.text}")
            raise

    def call_api(self, api_url: str, private_key_path: str, method: str = 'GET',
                headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """
        Call an NHS API with authentication

        Args:
            api_url: Full URL of the API endpoint
            private_key_path: Path to the private key PEM file
            method: HTTP method (GET, POST, etc.)
            headers: Additional headers to include
            **kwargs: Additional arguments to pass to requests (e.g., json, data, params)

        Returns:
            Response object
        """
        # Get access token
        access_token = self.get_access_token(private_key_path)

        # Prepare headers
        auth_headers = {
            "Authorization": f"Bearer {access_token}"
        }
        if headers:
            auth_headers.update(headers)

        # Make API call
        print(f"Calling API: {method} {api_url}")
        print(f"Headers: {auth_headers}")
        response = requests.request(method, api_url, headers=auth_headers, **kwargs)

        print(f"✓ Response status: {response.status_code}")
        return response


def main():
    parser = argparse.ArgumentParser(
        description='NHS API JWT Authentication Helper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate key pair and JWKS
    %(prog)s generate-keys --api-key YOUR_API_KEY --env int

    # Get access token
    %(prog)s get-token --api-key YOUR_API_KEY --env int --private-key int-1.pem

  # Call an API
  %(prog)s call-api --api-key YOUR_API_KEY --env sandbox --private-key int-1.pem \\
        --url https://sandbox.api.service.nhs.uk/hello-world/hello/application

    # Call an API with NHS number
    %(prog)s call-api --api-key YOUR_API_KEY --env int --private-key int-1.pem \\
        --url https://int.api.service.nhs.uk/eligibility-signposting-api/patient-check/123 \\
        --nhs-number 123

    # Call an API with custom headers
    %(prog)s call-api --api-key YOUR_API_KEY --env int --private-key int-1.pem \\
        --url https://int.api.service.nhs.uk/some-api/endpoint \\
        --header "X-Custom-Header: value" --header "Another-Header: value2"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Generate keys command
    gen_parser = subparsers.add_parser('generate-keys', help='Generate RSA key pair and JWKS')
    gen_parser.add_argument('--api-key', required=True, help='Your API key')
    gen_parser.add_argument('--env', choices=['dev', 'int', 'prod'], default='int',
                            help='Environment (default: int)')
    gen_parser.add_argument('--kid', help='Key identifier (default: {env}-1)')
    gen_parser.add_argument('--output-dir', default='.',
                            help='Output directory (default: current)')

    # Get token command
    token_parser = subparsers.add_parser('get-token', help='Get access token')
    token_parser.add_argument('--api-key', required=True, help='Your API key')
    token_parser.add_argument('--env', choices=['dev', 'int', 'prod'], default='int',
                                help='Environment (default: int)')
    token_parser.add_argument('--kid', help='Key identifier (default: {env}-1)')
    token_parser.add_argument('--private-key', required=True,
                                help='Path to private key PEM file')

    # Call API command
    api_parser = subparsers.add_parser('call-api', help='Call an API endpoint')
    api_parser.add_argument('--api-key', required=True, help='Your API key')
    api_parser.add_argument('--env', choices=['dev', 'int', 'prod', 'sandbox'], default='int',
                            help='Environment (default: int)')
    api_parser.add_argument('--kid', help='Key identifier (default: {env}-1)')
    api_parser.add_argument('--private-key', required=True,
                            help='Path to private key PEM file')
    api_parser.add_argument('--url', required=True, help='API endpoint URL')
    api_parser.add_argument('--method', default='GET', help='HTTP method (default: GET)')
    api_parser.add_argument('--nhs-number', dest='nhs_number', metavar='NHS_NUMBER',
                            help='NHS number to include in nhs-login-nhs-number header')
    api_parser.add_argument('--header', action='append', dest='headers',
                            help='Additional headers in format "Name: Value" (can be used multiple times)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Handle generate-keys command
    if args.command == 'generate-keys':
        auth = NHSAPIAuth(args.api_key, args.env, args.kid)
        private_key_path, public_key_path = auth.generate_key_pair(args.output_dir)
        jwks_path = Path(args.output_dir) / f"{auth.kid}.json"
        auth.generate_jwks(public_key_path, str(jwks_path))

        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("1. Upload the JWKS file to the developer portal OR host it yourself:")
        print(f"   JWKS file: {jwks_path}")
        print("\n2. If hosting yourself, update your application with the JWKS URL")
        print("\n3. IMPORTANT: Keep your private key secure and never share it:")
        print(f"   Private key: {private_key_path}")
        print("="*70)

    # Handle get-token command
    elif args.command == 'get-token':
        auth = NHSAPIAuth(args.api_key, args.env, args.kid)
        token = auth.get_access_token(args.private_key)
        print("\n" + "="*70)
        print(f"Access Token: {token}")
        print(f"Expires: {auth.token_expiry}")
        print("="*70)

    # Handle call-api command
    elif args.command == 'call-api':
        # For sandbox, we don't need the token endpoint
        if args.env == 'sandbox':
            env = 'int'  # Use int for token generation
        else:
            env = args.env

        auth = NHSAPIAuth(args.api_key, env, args.kid)

        # Build additional headers
        additional_headers = {}

        # Add NHS number header if provided
        if args.nhs_number:
            additional_headers['nhs-login-nhs-number'] = args.nhs_number

        # Add any custom headers
        if args.headers:
            for header in args.headers:
                if ':' in header:
                    name, value = header.split(':', 1)
                    additional_headers[name.strip()] = value.strip()
                else:
                    print(f"Warning: Ignoring invalid header format: {header}")

        response = auth.call_api(args.url, args.private_key, args.method,
                                headers=additional_headers if additional_headers else None)

        print("\n" + "="*70)
        print("RESPONSE:")
        print("="*70)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"\nBody:\n{response.text}")
        print("="*70)


if __name__ == "__main__":
    main()
