"""Live test: cart → checkout preview → optional place order flow."""

from __future__ import annotations

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
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main() -> int:
    print("=== Login ===")
    status, login = call(
        "POST", "/auth/login", {"email": "admin@rankplex.cloud", "password": "FoodStockAdmin2026"}
    )
    if status != 200:
        print("FAIL login", status, login)
        return 1
    token = login["data"]["access_token"]
    print("OK")

    print("\n=== Clear cart & add 2 variants (Kikkoman 250ml + 500ml) ===")
    call("DELETE", "/cart", token=token)
    for variant_id in (1, 2):
        status, body = call(
            "POST",
            "/cart/items",
            {"product_id": 1, "variant_id": variant_id, "quantity": 1, "replace": True},
            token=token,
        )
        if status != 201:
            print("FAIL add variant", variant_id, status, body)
            return 1
    print("OK")

    print("\n=== Addresses ===")
    status, addrs = call("GET", "/customer/addresses", token=token)
    if status != 200 or not addrs.get("data"):
        print("FAIL addresses", status, addrs)
        return 1
    address_id = addrs["data"][0]["id"]
    print("using address_id:", address_id)

    print("\n=== POST /checkout/preview ===")
    status, preview = call(
        "POST",
        "/checkout/preview",
        {"address_id": address_id, "payment_method": "cod"},
        token=token,
    )
    if status != 200:
        print("FAIL preview", status, preview)
        return 1
    data = preview["data"]
    bill = data["bill_summary"]
    cart = data["cart"]
    print("cart lines:", len(cart["items"]), "| item_count:", cart["item_count"])
    print("bill_summary:", json.dumps(bill, indent=2))

    errors = []
    if bill["line_count"] != 2:
        errors.append(f"line_count expected 2, got {bill['line_count']}")
    if bill["item_count"] != 2:
        errors.append(f"item_count expected 2, got {bill['item_count']}")
    if not bill["minimum_order_met"]:
        errors.append("minimum_order_met should be true")
    expected_subtotal = sum(float(i["line_total"]) for i in cart["items"])
    if float(bill["subtotal"]) != expected_subtotal:
        errors.append(f"subtotal mismatch {bill['subtotal']} vs {expected_subtotal}")
    if float(bill["total_amount"]) != float(bill["subtotal"]) + float(bill["tax_amount"]) + float(
        bill["delivery_fee"]
    ):
        errors.append("total_amount != subtotal + tax + delivery")

    print("\n=== GET /orders (list) ===")
    status, orders = call("GET", "/orders", token=token)
    if status != 200:
        print("FAIL list orders", status, orders)
        return 1
    print("existing orders:", len(orders["data"]))

    if errors:
        print("\nFAIL:")
        for err in errors:
            print(" -", err)
        return 1

    print("\n=== ALL CHECKOUT TESTS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
