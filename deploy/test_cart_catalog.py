"""Quick live test: add one cart item and verify catalog products response."""
import json
import sys
import urllib.error
import urllib.request

BASE = "https://rankplex.cloud/foodstock/api/v1"


def call(method: str, path: str, body=None, token=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main() -> int:
    print("=== 1. Login ===")
    status, login = call(
        "POST", "/auth/login", {"email": "admin@rankplex.cloud", "password": "FoodStockAdmin2026"}
    )
    if status != 200:
        print("FAIL login", status, login)
        return 1
    token = login["data"]["access_token"]
    print("OK")

    print("\n=== 2. Clear cart ===")
    status, cleared = call("DELETE", "/cart", token=token)
    if status != 200:
        print("FAIL clear", status, cleared)
        return 1
    print("item_count:", cleared["data"]["item_count"])

    print("\n=== 3. Add TWO variants of same product (variant 3 + variant 4) ===")
    for variant_id in (3, 4):
        status, added = call(
            "POST",
            "/cart/items",
            {"product_id": 2, "variant_id": variant_id, "quantity": 1, "replace": True},
            token=token,
        )
        if status != 201:
            print("FAIL add", variant_id, status, added)
            return 1
        print(f"  added variant {variant_id}: {added['data']['size']}")

    print("\n=== 4. GET /cart ===")
    status, cart = call("GET", "/cart", token=token)
    if status != 200:
        print("FAIL cart", status, cart)
        return 1
    items = cart["data"]["items"]
    print("lines:", len(items), "| item_count:", cart["data"]["item_count"])
    for item in items:
        print(
            f"  - variant {item['variant_id']} ({item['size']}) "
            f"qty={item['quantity']} total={item['line_total']}"
        )
    variant_ids = sorted(i["variant_id"] for i in items if i["product_id"] == 2)
    if variant_ids != [3, 4]:
        print("FAIL: expected variants 3 and 4 in cart, got", variant_ids)
        return 1
    if cart["data"]["item_count"] != 2:
        print("FAIL: expected item_count 2")
        return 1

    print("\n=== 5. GET /catalog/products ===")
    status, catalog = call("GET", "/catalog/products?page=1&page_size=20", token=token)
    if status != 200:
        print("FAIL catalog", status, catalog)
        return 1
    print("cart_info:", json.dumps(catalog["data"]["cart_info"], indent=2))
    if catalog["data"]["cart_info"]["item_count"] != 2:
        print("FAIL: cart_info.item_count should be 2")
        return 1

    product = next((p for p in catalog["data"]["items"] if p["id"] == 2), None)
    if not product:
        print("FAIL: product id 2 not in list")
        return 1
    print("product:", product["name"])
    print("  cart_added:", product.get("cart_added"))
    print("  variants_in_cart:", product.get("variants_in_cart"))
    print("  cart_quantity:", product.get("cart_quantity"))
    for variant in product["variants"]:
        print(
            f"  variant {variant['id']} {variant['size']}: "
            f"cart_added={variant['cart_added']} cart_quantity={variant['cart_quantity']}"
        )

    v3 = next(v for v in product["variants"] if v["id"] == 3)
    v4 = next(v for v in product["variants"] if v["id"] == 4)
    errors = []
    if product.get("cart_added") != "yes":
        errors.append("cart_added should be yes")
    if sorted(product.get("variants_in_cart", [])) != [3, 4]:
        errors.append("variants_in_cart should be [3, 4]")
    if product.get("cart_quantity") != 2:
        errors.append("cart_quantity should be 2")
    if v3["cart_added"] != "yes" or v3["cart_quantity"] != 1:
        errors.append("variant 3 should be in cart")
    if v4["cart_added"] != "yes" or v4["cart_quantity"] != 1:
        errors.append("variant 4 should be in cart")

    in_cart = [p["id"] for p in catalog["data"]["items"] if p.get("variants_in_cart")]
    print("products with variants in cart:", in_cart)
    if in_cart != [2]:
        errors.append(f"only product 2 should have variants in cart, got {in_cart}")

    if errors:
        print("\nFAIL:")
        for err in errors:
            print(" -", err)
        return 1

    print("\n=== ALL TESTS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
