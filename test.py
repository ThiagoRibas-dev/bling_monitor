import requests
import base64
import json
import os
import time # Import the time module
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
# You will only need this AUTH_CODE for the very first run.
AUTH_CODE = os.getenv("AUTH_CODE")
MINUTES_BETWEEN_RUNS = int(os.getenv("MINUTES_BETWEEN_RUNS", 5)) # Default to 5 minutes

TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
API_BASE = "https://www.bling.com.br/Api/v3"
TOKEN_FILE = "tokens.json"

# --- Global State ---
access_token = None
refresh_token = None

# --- Helper Functions ---
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
    global access_token, refresh_token
    access_token = tokens['access_token']
    refresh_token = tokens['refresh_token']
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)
    print("Tokens saved successfully.")

def load_tokens():
    """Loads tokens from a file if it exists."""
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None

# --- API Authentication ---
def get_initial_token():
    """Exchanges the one-time AUTH_CODE for the first token."""
    print("Attempting to get initial token with AUTH_CODE...")
    data = {
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": AUTH_CODE
    }
    headers = get_basic_auth_header()
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    tokens = response.json()
    save_tokens(tokens)
    return tokens

def refresh_access_token():
    """Refreshes the access token using the stored refresh token."""
    print("Refreshing access token...")
    global refresh_token
    if not refresh_token:
        raise ValueError("No refresh token available.")
        
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    headers = get_basic_auth_header()
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    tokens = response.json()
    # Bling might not always return a new refresh token, so we preserve the old one.
    if 'refresh_token' not in tokens:
        tokens['refresh_token'] = refresh_token
    save_tokens(tokens)
    return tokens

# --- API Core Logic ---
def get_products(page=1):
    """Fetches a paginated list of products from the Bling API."""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{API_BASE}/produtos?page={page}&limite=100"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:  # Token expired
        print("Access token expired. Refreshing...")
        refresh_access_token()
        headers = {"Authorization": f"Bearer {access_token}"} # Retry with new token
        response = requests.get(url, headers=headers)
        
    response.raise_for_status()
    return response.json()

def update_product(product_id, payload):
    """Updates a product's information on the Bling API."""
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    url = f"{API_BASE}/produtos/{product_id}"
    response = requests.patch(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 401:  # Token expired
        print("Access token expired. Refreshing...")
        refresh_access_token()
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"} # Retry with new token
        response = requests.patch(url, headers=headers, data=json.dumps(payload))
        
    response.raise_for_status()
    return response.json()

def find_and_deactivate_first_zero_stock_product():
    """Finds the first product with zero stock and sets its status to 'Inativo'."""
    print("\nSearching for the first product with zero stock to deactivate...")
    page = 1
    count = 0
    while True:
        if count > 100:
            return #Deal with 100 itens, then returns

        try:
            data = get_products(page)
            products = data.get("data", [])
            if not products:
                print("No more products to check.")
                break
            
            for p in products:
                stock = p.get("estoqueAtual", 0)
                if stock == 0:
                    product_id = p.get("id")
                    product_name = p.get("nome")
                    print(f"Found product with zero stock - ID: {product_id} | Name: {product_name}. Deactivating...")
                    
                    # Payload to set product status to 'Desativado'
                    payload = {"situacao": "I"}
                    update_product(product_id, payload)
                    print(f"Product ID: {product_id} | Name: {product_name} has been set to Inativo.")
            
            page += 1
        except requests.exceptions.HTTPError as e:
            print(f"An API error occurred: {e}")
            break
        count += 1
# --- Main Execution ---
if __name__ == "__main__":
    try:
        while True:
            loaded_tokens = load_tokens()
            if loaded_tokens:
                refresh_token = loaded_tokens['refresh_token']
                try:
                    refresh_access_token()
                except requests.exceptions.HTTPError as e:
                    print(f"Failed to refresh token: {e}. Please get a new AUTH_CODE.")
                    # As a fallback, you could delete tokens.json and re-run
            else:
                try:
                    get_initial_token()
                except requests.exceptions.HTTPError as e:
                    print(f"Failed to get initial token: {e}")
                    print("Please ensure your AUTH_CODE is new and valid.")

            if access_token:
                find_and_deactivate_first_zero_stock_product()
            else:
                print("\nCould not obtain access token. Exiting.")
            
            print(f"\nWaiting for {MINUTES_BETWEEN_RUNS} minutes before next run...")
            time.sleep(MINUTES_BETWEEN_RUNS * 60) # Convert minutes to seconds

    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting.")
