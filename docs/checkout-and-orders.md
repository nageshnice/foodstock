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
| `online_payment_not_available` | 400 | `payment_method` is `razorpay` |

---

## POST /orders

Same body as checkout preview. Creates the order, writes inventory SALE transactions, and clears the cart.

### Payment methods

| `payment_method` | Behaviour |
|------------------|-----------|
| `cod` | Order placed immediately; pay cash on delivery |
| `upi_on_delivery` | Order placed immediately; pay via UPI on delivery |
| `razorpay` | **Not available yet** — returns `400` with `online_payment_not_available` |

Response `data.payment` describes how to show payment status in the app:

| Field | Example (COD) | Description |
|-------|---------------|-------------|
| `method` | `cod` | Echo of request |
| `status` | `pay_on_delivery` | `pay_on_delivery` or `pending_online` |
| `label` | `Cash on delivery` | UI label |
| `requires_online_payment` | `false` | `true` when a gateway step would be required |

### Response `data` (order placed)

| Field | Description |
|-------|-------------|
| `id` | Order id |
| `order_number` | Human-readable order number (e.g. `ORD042817`) |
| `status` | Order status (starts as `pending`) |
| `payment_method` | Requested method |
| `payment` | Payment status for the UI (see above) |
| `subtotal`, `tax_amount`, `delivery_fee`, `total_amount` | Order totals (same rules as checkout preview) |
| `bill_summary` | Same shape as checkout preview |
| `delivery_address` | Formatted address string |
| `placed_at` | UTC timestamp |
| `items[]` | Line snapshots (see below) |

### Order line `items[]`

Each line is a snapshot at order time (prices do not change if catalog is updated later):

| Field | Description |
|-------|-------------|
| `variant_id` | Catalog variant id |
| `product_id` | Catalog product id |
| `product_name`, `brand_name`, `image_url` | Display fields |
| `variant_size` | Size label (e.g. `250ml`) |
| `unit_price`, `quantity`, `line_total` | Pricing |
| `tax_rate`, `tax_amount` | Tax per line |

### Inventory

For each line, stock is reduced and an `InventoryTransaction` of type `SALE` is recorded with note `Order {order_number}`.

### Errors (additional)

| Code | HTTP | When |
|------|------|------|
| `minimum_order_not_met` | 400 | Subtotal below minimum |
| `insufficient_stock` | 400 | Stock changed since cart was built |
| `online_payment_not_available` | 400 | `payment_method` is `razorpay` |

---

## GET /orders

Returns the authenticated customer’s orders, newest first.

## GET /orders/{order_id}

Single order with full `items[]` (variant/product ids, brand, image, unit price, tax, line total) plus `payment` and `bill_summary`.

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
