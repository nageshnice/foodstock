# Food Stock API and React Admin

First-phase quick-commerce platform for Japanese, Korean, Thai, Chinese, exotic, and spice
products. It includes customer authentication, catalog browsing, persistent carts, addresses,
checkout, stock-safe orders, order history, protected administration APIs, a React admin panel,
spreadsheet import, and a Postman collection.

## Technology

- Python 3.11+
- FastAPI
- MySQL (XAMPP)
- SQLAlchemy 2 with async sessions
- `aiomysql` MySQL driver
- Pydantic Settings
- Argon2 password hashing through `pwdlib`
- JWT signing and validation through PyJWT
- Alembic migrations
- React 19, TypeScript, Vite, and Material UI

## Project structure

```text
FoodStockAPI/
|-- app/
|   |-- core/           # Settings, logging, exceptions, security, and permissions
|   |-- database/       # SQLAlchemy base, async engine, and session lifecycle
|   |-- models/         # Commerce and account database models
|   |-- repositories/   # Feature data-access layer
|   |-- routers/        # Customer, commerce, and admin APIs
|   |-- schemas/        # Typed API contracts
|   |-- services/       # Transaction and business rules
|   |-- utils/          # Domain-independent constants and helpers
|   `-- main.py         # FastAPI application factory and middleware wiring
|-- admin/              # React administration panel
|-- alembic/            # Database migrations
|-- postman/            # Importable API collection
|-- scripts/            # Database, catalog, and admin setup commands
|-- tests/              # API, schema, and security tests
|-- .env.example        # Safe configuration template
|-- requirements.txt    # Runtime dependencies
|-- requirements-dev.txt
`-- pyproject.toml      # Test and lint configuration
```

The backend dependency direction is:

```text
router -> service -> repository -> model/database
          |              |
          `---- schemas -'
```

Routers should handle HTTP concerns, services should own business rules, and repositories
should be the only layer that performs feature-specific persistence operations.

## Local setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

For application use:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For development and testing:

```bash
pip install -r requirements-dev.txt
```

### 3. Prepare MySQL (XAMPP)

Start MySQL from the XAMPP control panel, then create the database:

```sql
CREATE DATABASE food_stock CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Apply the schema with `python -m scripts.create_tables` or `alembic upgrade head`.

### 4. Configure environment variables

Copy the example file:

```powershell
Copy-Item .env.example .env
```

On macOS/Linux, use `cp .env.example .env`.

Replace every placeholder secret before starting the API. A configuration example is:

```dotenv
APP_NAME=Food Stock API
APP_ENV=development
APP_DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=mysql+aiomysql://root:@localhost:3306/food_stock
DB_ECHO=false
JWT_SECRET=replace_with_a_unique_random_value_at_least_32_characters_long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
DEFAULT_TAX_RATE=5.00
DELIVERY_FEE=5.00
FREE_DELIVERY_THRESHOLD=499.00
MINIMUM_ORDER_AMOUNT=199.00
BOOTSTRAP_ADMIN_EMAIL=admin@your-domain.com
BOOTSTRAP_ADMIN_PASSWORD=replace_with_a_strong_unique_password
```

Generate a strong JWT secret instead of reusing the example value. `.env` is excluded from
Git and must never be committed. Production CORS origins should list only trusted web or
admin-panel domains.

## Import the Faridi Impex catalog

```powershell
python -m scripts.import_catalog "C:\Users\tnice\Downloads\Faridi_Impex_Products.xlsx"
```

The importer is idempotent by SKU and reads all 226 workbook rows. Since the source has no
prices, stock counts, SKU codes, or images, products and variants are imported as inactive
drafts with zero price and stock. Admin users must complete them before publishing. Worksheets
with reliable regions are assigned automatically; mixed First Choice rows remain unassigned
for review instead of being guessed.

Seed sample catalog data (regions, brands, products):

```powershell
python -m scripts.seed_catalog
```

Create the first super administrator after setting the bootstrap variables:

```powershell
python -m scripts.bootstrap_admin
```

Remove the bootstrap password from the runtime environment after the command succeeds.

## Run the API

```bash
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Verify it with:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "success": true,
  "message": "Food Stock API is healthy",
  "data": {
    "status": "healthy"
  }
}
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## API workflow

Signup and login return a JWT. Send it to every catalog, profile, address, cart, checkout,
order, and admin API as `Authorization: Bearer <access_token>`.

1. Load regions, brands, and products from `/api/v1/catalog`.
2. Add product variants to `/api/v1/cart/items`; the cart persists between sessions.
3. Maintain profile and delivery addresses.
4. Use `/api/v1/checkout/preview` for server-calculated price, tax, and delivery fee.
5. Place `/api/v1/orders`; stock is checked and decremented transactionally.
6. Use `/api/v1/orders` for the My Orders screen.

Phase one supports cash or UPI on delivery. Online payment, live maps, coupon rules,
notifications, and delivery-agent tracking are intentionally left for later phases.

## React admin panel

```powershell
Set-Location admin
Copy-Item .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`. Admin features include dashboard metrics, product publishing,
inventory adjustments, order status, users and roles, vendors, regions, categories, and brands.
Build production assets with `npm run build`.

## Postman

Import [Food_Stock_API.postman_collection.json](postman/Food_Stock_API.postman_collection.json).
Signup and Login automatically store the collection bearer token. Fill the provided entity ID
variables from list/create responses before running dependent requests.

## Quality checks

```bash
pytest -p no:cacheprovider
ruff check app scripts alembic tests --no-cache
ruff format --check app scripts alembic tests --no-cache
```

For the admin panel, run `npm run build` from `admin/`.

## Engineering conventions

- All runtime settings come from environment variables or `.env`.
- The API starts only when required database and JWT settings are present and valid.
- Database sessions commit successful request work and roll back failures.
- Successful and error responses use shared, typed envelopes.
- Expected application exceptions, HTTP errors, validation failures, and unexpected errors
  are mapped by centralized handlers.
- Password and JWT helpers contain no embedded secrets.
- Roles and permissions are centralized in `app/core/permissions.py`; public signup always
  creates a customer account.
- Product prices and order totals are authoritative on the server, never trusted from clients.
- Order creation and inventory deduction share one database transaction.

# foodstock
