"""
Módulo compartilhado para autenticação OAuth com Bling
Elimina duplicação de código entre test.py e dump_products.py
"""
import requests
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configurações
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
TOKEN_FILE = "tokens.json"

# Estado global
_tokens = None


def get_basic_auth_header():
    """Encodes Client ID and Secret for Basic Auth."""
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    return {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }


def save_tokens(tokens):
    """Saves access and refresh tokens to a file."""
    global _tokens
    _tokens = tokens
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)
    print("✅ Tokens saved successfully.")


def load_tokens():
    """Loads tokens from a file if it exists."""
    global _tokens
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, 'r') as f:
            _tokens = json.load(f)
            return _tokens
    except json.JSONDecodeError:
        return None


def get_initial_token(auth_code):
    """Exchanges the one-time AUTH_CODE for the first token."""
    print("🔑 Attempting to get initial token with AUTH_CODE...")
    data = {
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": auth_code
    }
    headers = get_basic_auth_header()
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    tokens = response.json()
    save_tokens(tokens)
    return tokens


def refresh_access_token():
    """Refreshes the access token using the stored refresh token."""
    global _tokens
    
    if not _tokens:
        _tokens = load_tokens()
    
    if not _tokens or 'refresh_token' not in _tokens:
        raise ValueError("No refresh token available. Run with AUTH_CODE first.")
    
    print("🔄 Refreshing access token...")
    data = {
        "grant_type": "refresh_token",
        "refresh_token": _tokens['refresh_token']
    }
    headers = get_basic_auth_header()
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    
    new_tokens = response.json()
    # Preserve refresh token if not returned
    if 'refresh_token' not in new_tokens:
        new_tokens['refresh_token'] = _tokens['refresh_token']
    
    save_tokens(new_tokens)
    return new_tokens


def get_access_token():
    """Returns a valid access token, refreshing if necessary."""
    global _tokens
    
    if not _tokens:
        _tokens = load_tokens()
    
    if not _tokens:
        auth_code = os.getenv("AUTH_CODE")
        if not auth_code:
            raise ValueError("No tokens found and no AUTH_CODE in .env")
        return get_initial_token(auth_code)['access_token']
    
    # Try to use current token, refresh if it fails (lazy refresh)
    return _tokens['access_token']


def ensure_authenticated():
    """Ensures valid authentication, returns access token."""
    try:
        return get_access_token()
    except:
        return refresh_access_token()['access_token']
