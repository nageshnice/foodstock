# Checkout and Orders API

Base path: `/api/v1`  
Auth: `Authorization: Bearer <access_token>`

## Flow

1. Add variants to cart — `POST /cart/items` (repeat per variant; multiple variants of one product are allowed).
2. Save a delivery address — `POST /customer/addresses`.
3. Preview checkout — `POST /checkout/preview`.
4. Place order — `POST /orders`.
5. View history — `GET /orders`, `GET /orders/{order_id}`.

## POST /checkout/preview

Calculates the checkout screen without placing an order.

### Request

```json
{
  "address_id": 1,
  "payment_method": "cod",
  "promo_code": null
}
```

| Field | Required | Values |
|-------|----------|--------|
| `address_id` | yes | From `GET /customer/addresses` → `data[].id` |
| `payment_method` | no (default `cod`) | `cod`, `upi_on_delivery`, `razorpay` |
| `promo_code` | no | Reserved for future use |

### Response `data`

| Field | Description |
|-------|-------------|
| `cart` | Full cart with `items[]`, `subtotal`, `tax_amount`, `delivery_fee`, `total_amount` |
| `address` | Selected delivery address |
| `payment_method` | Echo of request |
| `minimum_order_met` | `true` when subtotal ≥ minimum order (default ₹199) |
| `bill_summary` | Checkout totals for the bill summary UI |

### `bill_summary` (maps to checkout screen)

| Field | UI label |
|-------|----------|
| `line_count` | Badge “N ITEMS” (distinct variants) |
| `item_count` | Total units (sum of quantities) |
| `subtotal` | Subtotal |
| `delivery_fee` | Delivery fee (₹0 when subtotal ≥ free delivery threshold, default ₹499) |
| `tax_amount` | Tax (per-product tax rates) |
| `total_amount` | Place order total |
| `minimum_order_amount` | Minimum order rule |
| `minimum_order_met` | Whether checkout can proceed |
| `free_delivery_threshold` | Free delivery above this subtotal |

### Example (two variants, same product)

Cart: Kikkoman 250ml (₹189) + 500ml (₹329)

```json
{
  "bill_summary": {
    "item_count": 2,
    "line_count": 2,
    "subtotal": "518.00",
    "delivery_fee": "0.00",
    "tax_amount": "25.90",
    "total_amount": "543.90",
    "minimum_order_amount": "199.00",
    "minimum_order_met": true,
    "free_delivery_threshold": "499.00"
  }
}
```

### Errors

| Code | HTTP | When |
|------|------|------|
| `empty_cart` | 400 | No items in cart |
| `address_not_found` | 404 | Invalid `address_id` |

---

## POST /orders

Same body as checkout preview. Creates the order and clears the cart.

### Errors (additional)

| Code | HTTP | When |
|------|------|------|
| `minimum_order_not_met` | 400 | Subtotal below minimum |
| `insufficient_stock` | 400 | Stock changed since cart was built |

---

## GET /orders

Returns the authenticated customer’s orders, newest first.

## GET /orders/{order_id}

Single order with `items[]` (`product_name`, `variant_size`, `unit_price`, `quantity`, `line_total`).

---

## Cart item shape (in checkout `cart.items`)

Each line uses the variant id (not product id):

```json
{
  "id": 1,
  "variant_id": 1,
  "product_id": 1,
  "product_name": "Kikkoman Soy Sauce",
  "brand_name": "Kikkoman",
  "size": "250ml",
  "unit_price": "189.00",
  "quantity": 1,
  "line_total": "189.00"
}
```

## Add to cart (for checkout)

```json
POST /cart/items
{
  "product_id": 1,
  "variant_id": 1,
  "quantity": 1,
  "replace": false
}
```

Use `variants[].id` from `GET /catalog/products`, not the product `id`.
