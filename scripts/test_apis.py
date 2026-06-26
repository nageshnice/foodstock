# ruff: noqa: E501
"""
Live API test script - tests every endpoint with real data.
Run after the server is started: python scripts/test_apis.py
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://localhost:8000/api/v1"
PASS = []
FAIL = []


def req(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def check(label, status, body, expected=200):
    ok = status == expected
    symbol = "[PASS]" if ok else "[FAIL]"
    print(f"  {symbol} {label} -> HTTP {status}")
    if ok:
        PASS.append(label)
    else:
        FAIL.append(label)
        print(f"         Response: {json.dumps(body)[:200]}")
    return body.get("data") if ok else None


# ──────────────────────────────────────────────────────
# 1. Auth
# ──────────────────────────────────────────────────────
print("\n=== 1. AUTH ===")

# Admin login
s, b = req("POST", "/auth/login", {"email": "admin@example.com", "password": "admin123"})
data = check("Admin login", s, b)
admin_token = data["access_token"] if data else None
if data:
    print(f"         Admin int_id={data['user'].get('id', 'N/A')}, role={data['user']['role']}")

# Customer signup
s, b = req(
    "POST",
    "/auth/signup",
    {"email": "newtest@example.com", "password": "password123", "confirm_password": "password123"},
)
data = check("Customer signup", s, b, 201)
cust_token = data["access_token"] if data else None

# Customer login (existing)
s, b = req("POST", "/auth/login", {"email": "testcustomer@example.com", "password": "customer123"})
data = check("Customer login", s, b)
if data:
    cust_token = data["access_token"]
    print(f"         Customer int_id={data['user'].get('id', 'N/A')}")

# ──────────────────────────────────────────────────────
# 2. Customer Profile
# ──────────────────────────────────────────────────────
print("\n=== 2. PROFILE ===")

s, b = req("GET", "/customer/profile", token=cust_token)
data = check("GET profile", s, b)
if data:
    print(
        f"         id={data.get('id')}, email={data.get('email')}, image_url={'set' if data.get('image_url') else 'none'}"
    )

s, b = req(
    "PUT",
    "/customer/profile",
    {
        "full_name": "Test Customer Updated",
        "phone": "9876543299",
        "image_url": "https://ui-avatars.com/api/?name=Updated+Customer",
    },
    token=cust_token,
)
check("PUT profile (with image_url)", s, b)

# ──────────────────────────────────────────────────────
# 3. Catalog - Regions
# ──────────────────────────────────────────────────────
print("\n=== 3. CATALOG - REGIONS ===")

s, b = req("GET", "/catalog/regions", token=cust_token)
data = check("GET regions", s, b)
region_id = None
brand_id_for_region = None
if data:
    print(f"         total_count={data[0].get('total_count')}, regions:")
    for r in data:
        print(
            f"           id={r['id']}: {r['name']} | subtitle={r.get('subtitle', '?')} | products={r.get('product_count', 0)}"
        )
    region_id = data[0]["id"] if data else None

# ──────────────────────────────────────────────────────
# 4. Catalog - Brands (filtered by region)
# ──────────────────────────────────────────────────────
print("\n=== 4. CATALOG - BRANDS ===")

s, b = req("GET", "/catalog/brands", token=cust_token)
all_brands = check("GET all brands", s, b)
if all_brands:
    brand_summary = [str(br["id"]) + ":" + br["name"] for br in all_brands]
    print(f"         All brands: {brand_summary}")

if region_id:
    s, b = req("GET", f"/catalog/brands?region_id={region_id}", token=cust_token)
    filtered = check(f"GET brands filtered by region_id={region_id}", s, b)
    if filtered:
        filtered_summary = [str(br["id"]) + ":" + br["name"] for br in filtered]
        print(f"         Filtered brands: {filtered_summary}")
        brand_id_for_region = filtered[0]["id"] if filtered else None

# ──────────────────────────────────────────────────────
# 5. Catalog - Products
# ──────────────────────────────────────────────────────
print("\n=== 5. CATALOG - PRODUCTS ===")

s, b = req("GET", "/catalog/products", token=cust_token)
data = check("GET all products (paginated)", s, b)
first_product_id = None
first_variant_id = None
if data:
    items = data.get("items", [])
    print(f"         total={data['total']}, returned={len(items)}")
    if items:
        p = items[0]
        print(
            f"         First: id={p['id']}, name={p['name']}, variants={[v['id'] for v in p['variants']]}"
        )
        first_product_id = p["id"]
        first_variant_id = p["variants"][0]["id"] if p["variants"] else None

if region_id:
    s, b = req("GET", f"/catalog/products?region_id={region_id}", token=cust_token)
    data = check(f"GET products by region_id={region_id}", s, b)
    if data:
        print(f"         Region filter: {data['total']} products")

if region_id and brand_id_for_region:
    s, b = req(
        "GET",
        f"/catalog/products?region_id={region_id}&brand_id={brand_id_for_region}",
        token=cust_token,
    )
    data = check("GET products region+brand filter", s, b)
    if data:
        print(f"         Region+Brand filter: {data['total']} products")

if first_product_id:
    s, b = req("GET", f"/catalog/products/{first_product_id}", token=cust_token)
    data = check(f"GET product/{first_product_id}", s, b)
    if data:
        print(
            f"         Product: {data['name']}, region={data['region']['name'] if data.get('region') else 'none'}"
        )

# ──────────────────────────────────────────────────────
# 6. Catalog - Categories
# ──────────────────────────────────────────────────────
print("\n=== 6. CATALOG - CATEGORIES ===")

s, b = req("GET", "/catalog/categories", token=cust_token)
data = check("GET categories", s, b)
if data:
    cat_summary = [str(c["id"]) + ":" + c["name"] for c in data]
    print(f"         {cat_summary}")

# ──────────────────────────────────────────────────────
# 7. Customer Addresses
# ──────────────────────────────────────────────────────
print("\n=== 7. ADDRESSES ===")

s, b = req("GET", "/customer/addresses", token=cust_token)
data = check("GET addresses", s, b)
address_id = None
if data:
    print(f"         {len(data)} addresses found")
    if data:
        a = data[0]
        address_id = a["id"]
        print(
            f"         id={a['id']}, city={a.get('city')}, lat={a.get('latitude')}, lng={a.get('longitude')}"
        )

s, b = req(
    "POST",
    "/customer/addresses",
    {
        "address_type": "home",
        "house_flat_floor": "101, Tower B",
        "building_street": "Cyber Towers",
        "area_locality": "Hitech City",
        "city": "Hyderabad",
        "state": "Telangana",
        "pincode": "500081",
        "landmark": "Near metro station",
        "delivery_instructions": "Ring the bell twice",
        "latitude": "17.44920",
        "longitude": "78.38150",
        "is_default": False,
    },
    token=cust_token,
)
new_addr = check("POST create address (with coordinates)", s, b, 201)
if new_addr:
    print(
        f"         New address id={new_addr['id']}, lat={new_addr.get('latitude')}, lng={new_addr.get('longitude')}"
    )

# ──────────────────────────────────────────────────────
# 8. Cart
# ──────────────────────────────────────────────────────
print("\n=== 8. CART ===")

s, b = req("GET", "/cart", token=cust_token)
data = check("GET cart", s, b)

if first_variant_id:
    s, b = req(
        "POST", "/cart/items", {"variant_id": first_variant_id, "quantity": 2}, token=cust_token
    )
    data = check(f"POST add to cart (variant {first_variant_id})", s, b, 201)
    if data:
        print(
            f"         Cart: {data['item_count']} items, subtotal={data['subtotal']}, total={data['total_amount']}"
        )

# ──────────────────────────────────────────────────────
# 9. Admin - Dashboard
# ──────────────────────────────────────────────────────
print("\n=== 9. ADMIN - DASHBOARD ===")

s, b = req("GET", "/admin/dashboard", token=admin_token)
data = check("GET admin dashboard", s, b)
if data:
    print(
        f"         products={data['products']}, active={data['active_products']}, customers={data['customers']}, orders={data['orders']}"
    )

# ──────────────────────────────────────────────────────
# 10. Admin - Regions CRUD
# ──────────────────────────────────────────────────────
print("\n=== 10. ADMIN - REGIONS ===")

s, b = req("GET", "/admin/regions", token=admin_token)
data = check("GET admin regions", s, b)
admin_region_id = None
if data:
    print(
        f"         {len(data)} regions, first: id={data[0]['id']}, subtitle={data[0].get('subtitle')}, products={data[0].get('product_count')}"
    )
    admin_region_id = data[0]["id"]

s, b = req(
    "POST",
    "/admin/regions",
    {
        "name": "Mediterranean",
        "subtitle": "Sun-dried & artisan Mediterranean imports",
        "description": "Olive oils, herbs, and preserved goods from the Mediterranean",
        "is_active": True,
        "display_order": 10,
    },
    token=admin_token,
)
new_region = check("POST create region (with subtitle)", s, b, 201)
if new_region:
    print(
        f"         Created: id={new_region['id']}, name={new_region['name']}, subtitle={new_region.get('subtitle')}"
    )
    admin_region_id = new_region["id"]

if admin_region_id:
    s, b = req(
        "PUT",
        f"/admin/regions/{admin_region_id}",
        {
            "name": "Mediterranean",
            "subtitle": "Updated subtitle - premium Mediterranean imports",
            "description": "Updated description",
            "is_active": True,
            "display_order": 9,
        },
        token=admin_token,
    )
    check(f"PUT update region {admin_region_id}", s, b)

# ──────────────────────────────────────────────────────
# 11. Admin - Brands CRUD
# ──────────────────────────────────────────────────────
print("\n=== 11. ADMIN - BRANDS ===")

s, b = req("GET", "/admin/brands", token=admin_token)
data = check("GET admin brands", s, b)
admin_brand_id = None
if data:
    admin_brand_id = data[0]["id"]
    print(f"         {len(data)} brands, first: id={data[0]['id']}, name={data[0]['name']}")

s, b = req("POST", "/admin/brands", {"name": "Kewpie", "is_active": True}, token=admin_token)
new_brand = check("POST create brand", s, b, 201)
if new_brand:
    print(f"         Created: id={new_brand['id']}, name={new_brand['name']}")

# ──────────────────────────────────────────────────────
# 12. Admin - Categories CRUD
# ──────────────────────────────────────────────────────
print("\n=== 12. ADMIN - CATEGORIES ===")

s, b = req("GET", "/admin/categories", token=admin_token)
data = check("GET admin categories", s, b)
if data:
    cat2_summary = [str(c["id"]) + ":" + c["name"] for c in data]
    print(f"         {cat2_summary}")

s, b = req(
    "POST",
    "/admin/categories",
    {"name": "Sauces & Condiments", "is_active": True},
    token=admin_token,
)
new_cat = check("POST create category", s, b, 201)
if new_cat:
    print(f"         Created: id={new_cat['id']}")

# ──────────────────────────────────────────────────────
# 13. Admin - Products CRUD
# ──────────────────────────────────────────────────────
print("\n=== 13. ADMIN - PRODUCTS ===")

s, b = req("GET", "/admin/products", token=admin_token)
data = check("GET admin products", s, b)
admin_product_id = None
admin_variant_id = None
if data:
    print(f"         {len(data)} products total")
    # Find a fully seeded product
    for p in data:
        if p.get("region_id") and p["variants"]:
            admin_product_id = p["id"]
            admin_variant_id = p["variants"][0]["id"]
            print(
                f"         Using: id={p['id']}, name={p['name']}, region_id={p['region_id']}, brand_id={p['brand_id']}"
            )
            break

if region_id and all_brands:
    use_brand_id = all_brands[0]["id"]
    s, b = req(
        "POST",
        "/admin/products",
        {
            "sku": "FI-TEST-999",
            "name": "Test Product via Admin",
            "description": "Created by API test",
            "tax_rate": 5,
            "is_active": True,
            "region_id": region_id,
            "brand_id": use_brand_id,
            "variants": [
                {
                    "size": "200ml",
                    "price": 199,
                    "stock_quantity": 50,
                    "low_stock_threshold": 5,
                    "is_active": True,
                },
                {
                    "size": "500ml",
                    "price": 349,
                    "stock_quantity": 30,
                    "low_stock_threshold": 3,
                    "is_active": True,
                },
            ],
        },
        token=admin_token,
    )
    new_prod = check("POST create product (with int region_id/brand_id)", s, b, 201)
    if new_prod:
        print(
            f"         Created: id={new_prod['id']}, name={new_prod['name']}, region_id={new_prod['region_id']}"
        )

# ──────────────────────────────────────────────────────
# 14. Admin - Inventory
# ──────────────────────────────────────────────────────
print("\n=== 14. ADMIN - INVENTORY ===")

if admin_variant_id:
    s, b = req(
        "POST",
        f"/admin/inventory/{admin_variant_id}/adjust",
        {"quantity_change": 20, "note": "Restock from warehouse"},
        token=admin_token,
    )
    check(f"POST inventory adjust variant {admin_variant_id} (+20)", s, b)

    s, b = req(
        "POST",
        f"/admin/inventory/{admin_variant_id}/adjust",
        {"quantity_change": -5, "note": "Damage write-off"},
        token=admin_token,
    )
    check(f"POST inventory adjust variant {admin_variant_id} (-5)", s, b)

# ──────────────────────────────────────────────────────
# 15. Admin - Vendors
# ──────────────────────────────────────────────────────
print("\n=== 15. ADMIN - VENDORS ===")

s, b = req("GET", "/admin/vendors", token=admin_token)
data = check("GET admin vendors", s, b)
admin_vendor_id = None
if data:
    admin_vendor_id = data[0]["id"]
    print(f"         {len(data)} vendors, first: id={data[0]['id']}, name={data[0]['name']}")

s, b = req(
    "POST",
    "/admin/vendors",
    {
        "name": "Global Pantry Imports",
        "is_active": True,
        "contact_name": "John Smith",
        "email": "john@globalpantry.com",
        "phone": "+91-9900001111",
        "address": "Mumbai, Maharashtra 400001",
    },
    token=admin_token,
)
new_vendor = check("POST create vendor", s, b, 201)
if new_vendor:
    print(f"         Created: id={new_vendor['id']}, name={new_vendor['name']}")

if admin_vendor_id:
    s, b = req(
        "PUT",
        f"/admin/vendors/{admin_vendor_id}",
        {
            "name": "Faridi Impex Pvt. Ltd.",
            "is_active": True,
            "contact_name": "Raza Faridi",
            "email": "raza@faridiimpex.com",
            "phone": "+91-9876543210",
        },
        token=admin_token,
    )
    check(f"PUT update vendor {admin_vendor_id}", s, b)

# ──────────────────────────────────────────────────────
# 16. Admin - Customers
# ──────────────────────────────────────────────────────
print("\n=== 16. ADMIN - CUSTOMERS ===")

s, b = req("GET", "/admin/customers", token=admin_token)
data = check("GET admin customers", s, b)
admin_customer_id = None
if data:
    print(f"         {len(data)} customers")
    for c in data[:3]:
        print(
            f"           id={c['id']}, email={c['email']}, role={c['role']}, image_url={'set' if c.get('image_url') else 'none'}"
        )
    # Find a customer (not admin)
    for c in data:
        if c["role"] == "customer":
            admin_customer_id = c["id"]
            break

if admin_customer_id:
    s, b = req(
        "PATCH",
        f"/admin/customers/{admin_customer_id}",
        {"role": "customer", "is_active": True},
        token=admin_token,
    )
    check(f"PATCH update customer {admin_customer_id}", s, b)

# ──────────────────────────────────────────────────────
# 17. Admin - Orders
# ──────────────────────────────────────────────────────
print("\n=== 17. ADMIN - ORDERS ===")

s, b = req("GET", "/admin/orders", token=admin_token)
data = check("GET admin orders", s, b)
if data:
    print(f"         {len(data)} orders")

# ──────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────
print(f"\n{'=' * 50}")
print(f"RESULTS: {len(PASS)} PASSED, {len(FAIL)} FAILED")
if FAIL:
    print("\nFailed tests:")
    for f in FAIL:
        print(f"  - {f}")
print(f"{'=' * 50}\n")
sys.exit(0 if not FAIL else 1)
