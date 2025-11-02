import json
import os
import requests
import time

API_BASE = "https://api.bling.com.br/Api/v3"
OUTPUT_FILE = "products_dump.json"

def get_all_categories(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    all_categories = {}
    page = 1
    while True:
        url = f"{API_BASE}/categorias/produtos?pagina={page}&limite=100"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        categories = data.get("data", [])
        if not categories:
            break
        for cat in categories:
            all_categories[cat['id']] = cat
        page += 1
    print(f"Found {len(all_categories)} categories.")
    return all_categories

def get_category_prefix(category_name):
    parts = category_name.split()
    if len(parts) > 1:
        return (parts[0][:2] + parts[1][:2]).upper()
    else:
        return category_name[:4].upper()

def dump_all_products(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print("Fetching all categories...")
    categories = get_all_categories(access_token)
    category_counters = {}
    category_prefixes = {}

    all_products = []
    page = 1

    while True:
        url = f"{API_BASE}/produtos?pagina={page}&limite=100"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        products = data.get("data", [])
        if not products:
            break

        for product_summary in products:
            product_id = product_summary["id"]
            details_url = f"{API_BASE}/produtos/{product_id}"
            details_response = requests.get(details_url, headers=headers)
            details_response.raise_for_status()
            product_details = details_response.json().get("data", {})

            if 'categoria' not in product_details:
                continue

            if not product_details['codigo'] and product_details['categoria']['id'] in categories:
                cat_id = product_details['categoria']['id']
                cat = categories[cat_id]
                
                cat_name = cat_name['nome']
                if cat_id not in category_counters:
                    category_counters[cat_id] = 0
                
                if cat_id not in category_prefixes:
                    category_prefixes[cat_id] = get_category_prefix(cat_name)

                category_counters[cat_id] += 1
                prefix = category_prefixes[cat_id]
                counter = category_counters[cat_id]
                
                product_details['codigo'] = f"{prefix}{counter:05d}"
            
            all_products.append(product_details)
            time.sleep(0.4)

        print(f"Fetched page {page}, total so far: {len(all_products)}")
        page += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Dump saved to {OUTPUT_FILE} ({len(all_products)} products)")

if __name__ == "__main__":
    TOKEN_FILE = "tokens.json"
    if not os.path.exists(TOKEN_FILE):
        print(f"Error: Token file '{TOKEN_FILE}' not found.")
        print("Please run test.py first to generate the tokens.")
    else:
        with open(TOKEN_FILE, 'r') as f:
            try:
                tokens = json.load(f)
                access_token = tokens.get('access_token')
                if not access_token:
                    print("Error: Access token not found in tokens.json.")
                else:
                    dump_all_products(access_token)
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON from {TOKEN_FILE}.")
