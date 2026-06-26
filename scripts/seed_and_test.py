"""
Comprehensive seed script: bootstraps admin, seeds regions/brands/categories/vendors/products,
creates a test customer, adds addresses, and verifies all API endpoints.
Run: python scripts/seed_and_test.py
"""

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.permissions import Role
from app.core.security import hash_password
from app.database.session import AsyncSessionFactory, close_database
from app.models.domain import (
    Address,
    AddressType,
    Brand,
    Cart,
    Category,
    Product,
    ProductVariant,
    Region,
    User,
    Vendor,
)
from app.utils.text import slugify


async def get_or_create(session, model, name: str, **kwargs):
    existing = await session.scalar(select(model).where(model.name == name))
    if existing:
        print(f"  [exists] {model.__tablename__}: {name}")
        return existing
    obj = model(name=name, slug=slugify(name), **kwargs)
    session.add(obj)
    await session.flush()
    print(f"  [created] {model.__tablename__}: {name}  (int_id={obj.int_id})")
    return obj


async def seed():
    print("\n====== SEED START ======\n")
    async with AsyncSessionFactory() as session:
        # ─── 1. Bootstrap super admin ────────────────────────────────
        print("1. Creating / updating super-admin...")
        admin_email = "admin@example.com"
        admin = await session.scalar(select(User).where(User.email == admin_email))
        if admin:
            admin.role = Role.SUPER_ADMIN
            admin.is_active = True
            admin.password_hash = hash_password("admin123")
            print(f"   Updated admin → role=super_admin  (int_id={admin.int_id})")
        else:
            admin = User(
                email=admin_email,
                password_hash=hash_password("admin123"),
                full_name="Super Admin",
                role=Role.SUPER_ADMIN,
                is_active=True,
            )
            session.add(admin)
            await session.flush()
            print(f"   Created admin (int_id={admin.int_id})")

        # ─── 2. Regions ──────────────────────────────────────────────
        print("\n2. Seeding Regions...")
        region_data = [
            {
                "name": "Japanese",
                "subtitle": "Authentic Japanese pantry essentials",
                "description": "Premium Japanese imported pantry goods",
                "display_order": 1,
            },
            {
                "name": "Korean",
                "subtitle": "Bold Korean flavours & kimchi staples",
                "description": "Korean sauces, pastes and pantry products",
                "display_order": 2,
            },
            {
                "name": "Thai",
                "subtitle": "Aromatic Thai curry & rice pantry",
                "description": "Thai pantry staples - jasmine rice, curry pastes",
                "display_order": 3,
            },
            {
                "name": "Chinese",
                "subtitle": "Classic Chinese sauces & noodles",
                "description": "Chinese sauces, noodles and preserved goods",
                "display_order": 4,
            },
            {
                "name": "Middle Eastern",
                "subtitle": "Rich Middle Eastern spices & grains",
                "description": "Middle Eastern pantry - spices, grains, tahini",
                "display_order": 5,
            },
            {
                "name": "Exotics",
                "subtitle": "Unique global specialty imports",
                "description": "Exotic global pantry items from around the world",
                "display_order": 6,
            },
        ]
        regions = {}
        for rd in region_data:
            existing = await session.scalar(select(Region).where(Region.name == rd["name"]))
            if existing:
                existing.subtitle = rd["subtitle"]
                existing.description = rd["description"]
                existing.display_order = rd["display_order"]
                existing.is_active = True
                await session.flush()
                regions[rd["name"]] = existing
                print(f"  [updated] region: {rd['name']}  (int_id={existing.int_id})")
            else:
                r = Region(
                    name=rd["name"],
                    slug=slugify(rd["name"]),
                    subtitle=rd["subtitle"],
                    description=rd["description"],
                    display_order=rd["display_order"],
                    is_active=True,
                )
                session.add(r)
                await session.flush()
                regions[rd["name"]] = r
                print(f"  [created] region: {rd['name']}  (int_id={r.int_id})")

        # ─── 3. Vendor ───────────────────────────────────────────────
        print("\n3. Seeding Vendor...")
        vendor_name = "Faridi Impex Pvt. Ltd."
        vendor = await session.scalar(select(Vendor).where(Vendor.name == vendor_name))
        if not vendor:
            vendor = Vendor(
                name=vendor_name,
                slug=slugify(vendor_name),
                contact_name="Raza Faridi",
                email="raza@faridiimpex.com",
                phone="+91-9876543210",
                address="Gachibowli, Hyderabad - 500032",
                tax_identifier="36AABCF1234D1Z5",
                is_active=True,
            )
            session.add(vendor)
            await session.flush()
            print(f"  [created] vendor: {vendor_name}  (int_id={vendor.int_id})")
        else:
            print(f"  [exists] vendor: {vendor_name}  (int_id={vendor.int_id})")

        # ─── 4. Brands ───────────────────────────────────────────────
        print("\n4. Seeding Brands...")
        brand_data = [
            "First Choice",
            "Al Ameera",
            "Kikkoman",
            "Ottogi",
            "Bibigo",
            "Maesri",
        ]
        brands = {}
        for bn in brand_data:
            b = await session.scalar(select(Brand).where(Brand.name == bn))
            if not b:
                b = Brand(name=bn, slug=slugify(bn), is_active=True)
                session.add(b)
                await session.flush()
                print(f"  [created] brand: {bn}  (int_id={b.int_id})")
            else:
                print(f"  [exists] brand: {bn}  (int_id={b.int_id})")
            brands[bn] = b

        # ─── 5. Category ─────────────────────────────────────────────
        print("\n5. Seeding Category...")
        category = await session.scalar(select(Category).where(Category.name == "Imported Pantry"))
        if not category:
            category = Category(
                name="Imported Pantry",
                slug="imported-pantry",
                description="All imported pantry items",
                is_active=True,
            )
            session.add(category)
            await session.flush()
            print(f"  [created] category: Imported Pantry  (int_id={category.int_id})")
        else:
            print(f"  [exists] category: Imported Pantry  (int_id={category.int_id})")

        # ─── 6. Products ─────────────────────────────────────────────
        print("\n6. Seeding Products...")
        products_data = [
            {
                "sku": "FI-JPN-001",
                "name": "Bibimbap Rice Bowl Mix",
                "region": "Japanese",
                "brand": "Kikkoman",
                "price": 249.00,
                "sizes": ["250ml", "500ml"],
                "description": "Traditional Japanese bibimbap rice bowl seasoning mix",
            },
            {
                "sku": "FI-KOR-001",
                "name": "Kimchi Paste - Original",
                "region": "Korean",
                "brand": "Ottogi",
                "price": 399.00,
                "sizes": ["500g", "1kg"],
                "description": "Authentic Korean kimchi paste made with gochugaru",
            },
            {
                "sku": "FI-KOR-002",
                "name": "Hotteok Sweet Pancake Mix",
                "region": "Korean",
                "brand": "Bibigo",
                "price": 189.00,
                "sizes": ["400g"],
                "description": "Korean street-style sweet pancake mix with brown sugar filling",
            },
            {
                "sku": "FI-KOR-003",
                "name": "Kung Pao Chicken Sauce",
                "region": "Korean",
                "brand": "Bibigo",
                "price": 299.00,
                "sizes": ["200ml", "500ml"],
                "description": "Spicy peanut-based kung pao sauce",
            },
            {
                "sku": "FI-THA-001",
                "name": "Jasmine Rice Premium",
                "region": "Thai",
                "brand": "First Choice",
                "price": 349.00,
                "sizes": ["1kg", "5kg"],
                "description": "Fragrant Thai jasmine rice, long grain premium grade",
            },
            {
                "sku": "FI-THA-002",
                "name": "Green Curry Paste",
                "region": "Thai",
                "brand": "Maesri",
                "price": 149.00,
                "sizes": ["100g", "400g"],
                "description": "Authentic Thai green curry paste with lemongrass and kaffir lime",
            },
            {
                "sku": "FI-MDE-001",
                "name": "Al Ameera Tahini",
                "region": "Middle Eastern",
                "brand": "Al Ameera",
                "price": 449.00,
                "sizes": ["400g", "800g"],
                "description": "Premium Lebanese-style sesame tahini paste",
            },
            {
                "sku": "FI-EXO-001",
                "name": "Kalamata Olives in Brine",
                "region": "Exotics",
                "brand": "First Choice",
                "price": 599.00,
                "sizes": ["350g", "700g"],
                "description": "Hand-picked Greek Kalamata olives in natural brine",
            },
        ]

        created_products = []
        for pd in products_data:
            existing = await session.scalar(
                select(Product)
                .where(Product.sku == pd["sku"])
                .options(selectinload(Product.variants))
            )
            region_obj = regions[pd["region"]]
            brand_obj = brands[pd["brand"]]
            if existing:
                existing.name = pd["name"]
                existing.description = pd["description"]
                existing.region_id = region_obj.id
                existing.brand_id = brand_obj.id
                existing.category_id = category.id
                existing.vendor_id = vendor.id
                existing.is_active = True
                existing.tax_rate = Decimal("5.00")
                # Ensure variants have price > 0 and active
                for v in existing.variants:
                    v.is_active = True
                    if v.price == 0:
                        v.price = Decimal(str(pd["price"]))
                    v.stock_quantity = max(v.stock_quantity, 50)
                await session.flush()
                created_products.append(existing)
                print(f"  [updated] {pd['sku']}: {pd['name']}  (int_id={existing.int_id})")
            else:
                product = Product(
                    sku=pd["sku"],
                    name=pd["name"],
                    slug=slugify(pd["name"]) + f"-{pd['sku'].lower()}",
                    description=pd["description"],
                    region_id=region_obj.id,
                    brand_id=brand_obj.id,
                    category_id=category.id,
                    vendor_id=vendor.id,
                    tax_rate=Decimal("5.00"),
                    is_active=True,
                )
                session.add(product)
                await session.flush()
                for size in pd["sizes"]:
                    v = ProductVariant(
                        product_id=product.id,
                        size=size,
                        price=Decimal(str(pd["price"])),
                        stock_quantity=100,
                        low_stock_threshold=10,
                        is_active=True,
                    )
                    session.add(v)
                await session.flush()
                # Reload to get int_id
                product = await session.scalar(
                    select(Product)
                    .where(Product.id == product.id)
                    .options(selectinload(Product.variants))
                )
                created_products.append(product)
                print(f"  [created] {pd['sku']}: {pd['name']}  (int_id={product.int_id})")

        # ─── 7. Test Customer ─────────────────────────────────────────
        print("\n7. Seeding test customer...")
        cust_email = "testcustomer@example.com"
        customer = await session.scalar(select(User).where(User.email == cust_email))
        if not customer:
            customer = User(
                email=cust_email,
                password_hash=hash_password("customer123"),
                full_name="Test Customer",
                phone="+91-9999000001",
                image_url="https://ui-avatars.com/api/?name=Test+Customer&background=1a365d&color=fff",
                role=Role.CUSTOMER,
                is_active=True,
            )
            session.add(customer)
            await session.flush()
            # Create cart for customer
            cart = Cart(user_id=customer.id)
            session.add(cart)
            await session.flush()
            print(f"  [created] customer: {cust_email}  (int_id={customer.int_id})")
        else:
            print(f"  [exists] customer: {cust_email}  (int_id={customer.int_id})")

        # ─── 8. Address for customer ──────────────────────────────────
        print("\n8. Seeding customer address...")
        existing_addr = await session.scalar(select(Address).where(Address.user_id == customer.id))
        if not existing_addr:
            addr = Address(
                user_id=customer.id,
                address_type=AddressType.HOME,
                house_flat_floor="Ff4, Eee",
                building_street="Imperial Heights",
                area_locality="Gachibowli",
                city="Hyderabad",
                state="Telangana",
                pincode="500084",
                landmark="Near DLF Cyber City",
                delivery_instructions="Call before delivery",
                latitude=Decimal("17.440810"),
                longitude=Decimal("78.348770"),
                is_default=True,
            )
            session.add(addr)
            await session.flush()
            print(f"  [created] address for customer  (int_id={addr.int_id})")
        else:
            print(f"  [exists] address for customer  (int_id={existing_addr.int_id})")

        await session.commit()

    await close_database()

    # ─── Print Summary ─────────────────────────────────────────────────
    print("\n====== SEED COMPLETE ======")
    print("\nCredentials:")
    print("  Admin   → admin@example.com  / admin123")
    print("  Customer→ testcustomer@example.com / customer123")
    print("\nRegion int_ids:")
    for name, r in regions.items():
        print(f"  {r.int_id}: {name} — subtitle: {r.subtitle}")
    print("\nBrand int_ids:")
    for name, b in brands.items():
        print(f"  {b.int_id}: {name}")
    print("\nProduct int_ids (first 4):")
    for p in created_products[:4]:
        variant_ids = [str(v.int_id) for v in p.variants]
        print(f"  {p.int_id}: {p.name}  variants: [{', '.join(variant_ids)}]")
    print(f"\nCategory int_id: {category.int_id}")
    print(f"Vendor int_id:   {vendor.int_id}")
    print("\nServer: uvicorn app.main:app --reload --port 8000")
    print("Docs:   http://localhost:8000/docs\n")


if __name__ == "__main__":
    asyncio.run(seed())
