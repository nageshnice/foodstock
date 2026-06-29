"""Regenerate Food_Stock_API.postman_collection.json from app routes."""

from __future__ import annotations

import json
from pathlib import Path

AUTH = [{"key": "Authorization", "value": "Bearer {{token}}", "type": "text"}]
JSON_CT = {"key": "Content-Type", "value": "application/json"}

SAVE_TOKEN_SIGNUP = [
    {
        "listen": "test",
        "script": {
            "exec": [
                "if (pm.response.code === 201) {",
                "  const data = pm.response.json().data;",
                "  pm.collectionVariables.set('token', data.access_token);",
                "  if (data.api_key) pm.collectionVariables.set('api_key', data.api_key);",
                "}",
            ]
        },
    }
]

SAVE_TOKEN_LOGIN = [
    {
        "listen": "test",
        "script": {
            "exec": [
                "if (pm.response.code === 200) {",
                "  const data = pm.response.json().data;",
                "  pm.collectionVariables.set('token', data.access_token);",
                "  if (data.api_key) pm.collectionVariables.set('api_key', data.api_key);",
                "}",
            ]
        },
    }
]


def req(
    name: str,
    method: str,
    url: str,
    body: str | None = None,
    *,
    auth: bool = True,
    noauth: bool = False,
    events: list | None = None,
) -> dict:
    item: dict = {"name": name, "request": {"method": method, "url": url}}
    headers: list[dict] = []
    if noauth:
        item["request"]["auth"] = {"type": "noauth"}
    elif auth:
        headers = list(AUTH)
    if body is not None:
        item["request"]["body"] = {"mode": "raw", "raw": body}
        headers = headers + [JSON_CT]
    if headers:
        item["request"]["header"] = headers
    if events:
        item["event"] = events
    return item


def main() -> None:
    collection = {
        "info": {
            "_postman_id": "4ea78df5-31e2-44a7-9f20-foodstockapi",
            "name": "Food Stock API",
            "description": (
                "Complete API collection for customer mobile flow and admin panel. "
                "Run Signup or Login first; test scripts save bearer token and API key automatically. "
                "Health check uses {{health_url}} (no /api/v1 prefix)."
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{token}}", "type": "string"}],
        },
        "variable": [
            {"key": "base_url", "value": "http://127.0.0.1:8000/api/v1"},
            {"key": "health_url", "value": "http://127.0.0.1:8000"},
            {"key": "token", "value": ""},
            {"key": "api_key", "value": ""},
            {"key": "product_id", "value": ""},
            {"key": "variant_id", "value": ""},
            {"key": "cart_item_id", "value": ""},
            {"key": "address_id", "value": ""},
            {"key": "order_id", "value": ""},
            {"key": "region_id", "value": ""},
            {"key": "category_id", "value": ""},
            {"key": "brand_id", "value": ""},
            {"key": "vendor_id", "value": ""},
            {"key": "customer_id", "value": ""},
        ],
        "item": [
            {
                "name": "Health",
                "item": [
                    req(
                        "Health Check",
                        "GET",
                        "{{health_url}}/health",
                        auth=False,
                        noauth=True,
                    )
                ],
            },
            {
                "name": "Authentication",
                "item": [
                    req(
                        "Signup",
                        "POST",
                        "{{base_url}}/auth/signup",
                        '{\n  "email": "customer@example.com",\n  "password": "StrongPassword123!",\n  "confirm_password": "StrongPassword123!"\n}',
                        auth=False,
                        noauth=True,
                        events=SAVE_TOKEN_SIGNUP,
                    ),
                    req(
                        "Login",
                        "POST",
                        "{{base_url}}/auth/login",
                        '{\n  "email": "customer@example.com",\n  "password": "StrongPassword123!"\n}',
                        auth=False,
                        noauth=True,
                        events=SAVE_TOKEN_LOGIN,
                    ),
                    req("Logout", "POST", "{{base_url}}/auth/logout"),
                ],
            },
            {
                "name": "Catalog",
                "item": [
                    req("Regions", "GET", "{{base_url}}/catalog/regions"),
                    req("Categories", "GET", "{{base_url}}/catalog/categories"),
                    req(
                        "Brands",
                        "GET",
                        "{{base_url}}/catalog/brands?region_id={{region_id}}",
                    ),
                    req(
                        "Products with Filters",
                        "GET",
                        "{{base_url}}/catalog/products?region_id={{region_id}}&category_id={{category_id}}&brand_id={{brand_id}}&search=&page=1&page_size=20",
                    ),
                    req(
                        "Product Detail",
                        "GET",
                        "{{base_url}}/catalog/products/{{product_id}}",
                    ),
                ],
            },
            {
                "name": "Profile and Addresses",
                "item": [
                    req("My Profile", "GET", "{{base_url}}/customer/profile"),
                    req(
                        "Update Profile",
                        "PATCH",
                        "{{base_url}}/customer/profile",
                        '{\n  "full_name": "Food Stock Customer",\n  "phone": "9876543210"\n}',
                    ),
                    req("Saved Addresses", "GET", "{{base_url}}/customer/addresses"),
                    req(
                        "Add Address",
                        "POST",
                        "{{base_url}}/customer/addresses",
                        '{\n  "address_type": "home",\n  "house_flat_floor": "8-16-1",\n  "building_street": "Nagarjuna Sagar Road",\n  "area_locality": "Kondapur",\n  "city": "Hyderabad",\n  "state": "Telangana",\n  "pincode": "500035",\n  "delivery_instructions": "Call on arrival",\n  "is_default": true\n}',
                    ),
                    req(
                        "Update Address",
                        "PUT",
                        "{{base_url}}/customer/addresses/{{address_id}}",
                        '{\n  "address_type": "home",\n  "house_flat_floor": "8-16-1",\n  "area_locality": "Kondapur",\n  "city": "Hyderabad",\n  "state": "Telangana",\n  "pincode": "500035",\n  "is_default": true\n}',
                    ),
                    req(
                        "Set Default Address",
                        "PATCH",
                        "{{base_url}}/customer/addresses/{{address_id}}/default",
                    ),
                    req(
                        "Delete Address",
                        "DELETE",
                        "{{base_url}}/customer/addresses/{{address_id}}",
                    ),
                ],
            },
            {
                "name": "Cart and Checkout",
                "item": [
                    req("View Cart", "GET", "{{base_url}}/cart"),
                    req(
                        "Add to Cart",
                        "POST",
                        "{{base_url}}/cart/items",
                        '{\n  "variant_id": {{variant_id}},\n  "quantity": 1\n}',
                    ),
                    req(
                        "Change Cart Quantity",
                        "PATCH",
                        "{{base_url}}/cart/items/{{cart_item_id}}",
                        '{\n  "quantity": 2\n}',
                    ),
                    req(
                        "Remove Cart Item",
                        "DELETE",
                        "{{base_url}}/cart/items/{{cart_item_id}}",
                    ),
                    req(
                        "Checkout Preview",
                        "POST",
                        "{{base_url}}/checkout/preview",
                        '{\n  "address_id": {{address_id}},\n  "payment_method": "upi_on_delivery"\n}',
                    ),
                    req(
                        "Place Order",
                        "POST",
                        "{{base_url}}/orders",
                        '{\n  "address_id": {{address_id}},\n  "payment_method": "upi_on_delivery"\n}',
                    ),
                    req("My Orders", "GET", "{{base_url}}/orders"),
                    req("Order Detail", "GET", "{{base_url}}/orders/{{order_id}}"),
                ],
            },
            {
                "name": "Admin",
                "item": [
                    {
                        "name": "Dashboard and Profile",
                        "item": [
                            req("Dashboard", "GET", "{{base_url}}/admin/dashboard"),
                            req("Admin Profile (Me)", "GET", "{{base_url}}/admin/me"),
                            req("Alerts", "GET", "{{base_url}}/admin/alerts"),
                            req(
                                "Events Stream (SSE)",
                                "GET",
                                "{{base_url}}/admin/events/stream?token={{token}}",
                                auth=False,
                            ),
                        ],
                    },
                    {
                        "name": "Regions",
                        "item": [
                            req("List Regions", "GET", "{{base_url}}/admin/regions"),
                            req(
                                "Create Region",
                                "POST",
                                "{{base_url}}/admin/regions",
                                '{\n  "name": "Europe",\n  "subtitle": "Imported goods",\n  "description": "European pantry items",\n  "is_active": true,\n  "display_order": 1\n}',
                            ),
                            req(
                                "Update Region",
                                "PUT",
                                "{{base_url}}/admin/regions/{{region_id}}",
                                '{\n  "name": "Europe",\n  "subtitle": "Updated subtitle",\n  "is_active": true,\n  "display_order": 1\n}',
                            ),
                            req(
                                "Delete Region",
                                "DELETE",
                                "{{base_url}}/admin/regions/{{region_id}}",
                            ),
                        ],
                    },
                    {
                        "name": "Categories",
                        "item": [
                            req("List Categories", "GET", "{{base_url}}/admin/categories"),
                            req(
                                "Create Category",
                                "POST",
                                "{{base_url}}/admin/categories",
                                '{\n  "name": "Snacks",\n  "description": "Packaged snacks",\n  "is_active": true\n}',
                            ),
                            req(
                                "Update Category",
                                "PUT",
                                "{{base_url}}/admin/categories/{{category_id}}",
                                '{\n  "name": "Snacks",\n  "description": "Updated description",\n  "is_active": true\n}',
                            ),
                            req(
                                "Delete Category",
                                "DELETE",
                                "{{base_url}}/admin/categories/{{category_id}}",
                            ),
                        ],
                    },
                    {
                        "name": "Brands",
                        "item": [
                            req(
                                "List Brands",
                                "GET",
                                "{{base_url}}/admin/brands?region_id={{region_id}}",
                            ),
                            req(
                                "Create Brand",
                                "POST",
                                "{{base_url}}/admin/brands",
                                '{\n  "name": "Demo Brand",\n  "region_id": {{region_id}},\n  "logo_url": null,\n  "is_active": true\n}',
                            ),
                            req(
                                "Update Brand",
                                "PUT",
                                "{{base_url}}/admin/brands/{{brand_id}}",
                                '{\n  "name": "Demo Brand",\n  "region_id": {{region_id}},\n  "logo_url": null,\n  "is_active": true\n}',
                            ),
                            req(
                                "Delete Brand",
                                "DELETE",
                                "{{base_url}}/admin/brands/{{brand_id}}",
                            ),
                        ],
                    },
                    {
                        "name": "Products",
                        "item": [
                            req("List Products", "GET", "{{base_url}}/admin/products"),
                            req(
                                "Create Product",
                                "POST",
                                "{{base_url}}/admin/products",
                                '{\n  "sku": "FI-DEMO-001",\n  "name": "Imported Pantry Demo",\n  "tax_rate": 5,\n  "is_active": true,\n  "region_id": {{region_id}},\n  "category_id": {{category_id}},\n  "brand_id": {{brand_id}},\n  "vendor_id": {{vendor_id}},\n  "variants": [{ "size": "500 Gm", "mrp": 349, "price": 299, "stock_quantity": 25, "low_stock_threshold": 5, "is_active": true }]\n}',
                            ),
                            req(
                                "Update Product",
                                "PUT",
                                "{{base_url}}/admin/products/{{product_id}}",
                                '{\n  "sku": "FI-DEMO-001",\n  "name": "Imported Pantry Demo Updated",\n  "tax_rate": 5,\n  "is_active": true,\n  "region_id": {{region_id}},\n  "category_id": {{category_id}},\n  "brand_id": {{brand_id}},\n  "vendor_id": {{vendor_id}},\n  "variants": [{ "size": "500 Gm", "mrp": 399, "price": 349, "stock_quantity": 25, "low_stock_threshold": 5, "is_active": true }]\n}',
                            ),
                            req(
                                "Deactivate Product",
                                "DELETE",
                                "{{base_url}}/admin/products/{{product_id}}",
                            ),
                            {
                                "name": "Upload Product Image",
                                "request": {
                                    "method": "POST",
                                    "header": AUTH,
                                    "body": {
                                        "mode": "formdata",
                                        "formdata": [
                                            {"key": "file", "type": "file", "src": ""}
                                        ],
                                    },
                                    "url": "{{base_url}}/admin/products/upload-image",
                                },
                            },
                        ],
                    },
                    {
                        "name": "Inventory",
                        "item": [
                            req(
                                "Adjust Inventory",
                                "POST",
                                "{{base_url}}/admin/inventory/{{variant_id}}/adjust",
                                '{\n  "quantity_change": 10,\n  "note": "New supplier delivery"\n}',
                            ),
                        ],
                    },
                    {
                        "name": "Orders",
                        "item": [
                            req("List Orders", "GET", "{{base_url}}/admin/orders"),
                            req(
                                "Update Order Status",
                                "PATCH",
                                "{{base_url}}/admin/orders/{{order_id}}/status",
                                '{ "status": "confirmed" }',
                            ),
                        ],
                    },
                    {
                        "name": "Customers",
                        "item": [
                            req("List Customers", "GET", "{{base_url}}/admin/customers"),
                            req(
                                "Create Customer",
                                "POST",
                                "{{base_url}}/admin/customers",
                                '{\n  "email": "newcustomer@example.com",\n  "password": "StrongPassword123!",\n  "full_name": "New Customer",\n  "phone": "9876543210",\n  "role": "customer",\n  "is_active": true\n}',
                            ),
                            req(
                                "Update Customer",
                                "PATCH",
                                "{{base_url}}/admin/customers/{{customer_id}}",
                                '{ "role": "customer", "is_active": true }',
                            ),
                            req(
                                "Delete Customer",
                                "DELETE",
                                "{{base_url}}/admin/customers/{{customer_id}}",
                            ),
                        ],
                    },
                    {
                        "name": "Vendors",
                        "item": [
                            req("List Vendors", "GET", "{{base_url}}/admin/vendors"),
                            req(
                                "Create Vendor",
                                "POST",
                                "{{base_url}}/admin/vendors",
                                '{\n  "name": "Faridi Impex Pvt. Ltd.",\n  "contact_name": "Operations",\n  "email": "operations@example.com",\n  "phone": "9876543210",\n  "is_active": true\n}',
                            ),
                            req(
                                "Update Vendor",
                                "PUT",
                                "{{base_url}}/admin/vendors/{{vendor_id}}",
                                '{\n  "name": "Faridi Impex Pvt. Ltd.",\n  "contact_name": "Operations",\n  "email": "operations@example.com",\n  "phone": "9876543210",\n  "is_active": true\n}',
                            ),
                        ],
                    },
                ],
            },
        ],
    }

    out = Path(__file__).with_name("Food_Stock_API.postman_collection.json")
    out.write_text(json.dumps(collection, indent=4) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
