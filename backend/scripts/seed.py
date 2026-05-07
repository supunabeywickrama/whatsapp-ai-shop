"""Seed the shop with default categories, brands, a sample product, and the
bootstrap admin user. Run from the backend container:

    python -m scripts.seed
"""

import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.admin import AdminRole, AdminUser
from app.models.catalog import Brand, Category, Product, ProductCondition


CATEGORIES = [
    "New Phones", "Used Phones", "Chargers", "Headsets",
    "Cables", "Tempered Glass", "Back Covers", "Accessories",
]

BRANDS = ["Apple", "Samsung", "Xiaomi", "Huawei", "OnePlus", "Realme", "Oppo", "Vivo"]


async def seed():
    async with SessionLocal() as db:
        # Categories
        cat_map: dict[str, Category] = {}
        for i, name in enumerate(CATEGORIES):
            res = await db.execute(select(Category).where(Category.name == name))
            c = res.scalar_one_or_none()
            if not c:
                c = Category(name=name, sort_order=i)
                db.add(c)
                await db.flush()
            cat_map[name] = c

        # Brands
        brand_map: dict[str, Brand] = {}
        for name in BRANDS:
            res = await db.execute(select(Brand).where(Brand.name == name))
            b = res.scalar_one_or_none()
            if not b:
                b = Brand(name=name)
                db.add(b)
                await db.flush()
            brand_map[name] = b

        # Sample product
        sku = "SAMS-CHG-25W"
        res = await db.execute(select(Product).where(Product.sku == sku))
        if not res.scalar_one_or_none():
            db.add(Product(
                sku=sku,
                title="Samsung 25W USB-C Fast Charger",
                description="Original Samsung 25W super-fast charging adapter with USB-C cable.",
                condition=ProductCondition.new,
                price=Decimal("4500.00"),
                stock_qty=20,
                images=[],
                specs={"wattage": "25W", "connector": "USB-C", "color": "white"},
                category_id=cat_map["Chargers"].id,
                brand_id=brand_map["Samsung"].id,
            ))

        # Bootstrap admin
        res = await db.execute(select(AdminUser).where(AdminUser.email == settings.ADMIN_BOOTSTRAP_EMAIL))
        if not res.scalar_one_or_none():
            db.add(AdminUser(
                email=settings.ADMIN_BOOTSTRAP_EMAIL,
                password_hash=hash_password(settings.ADMIN_BOOTSTRAP_PASSWORD),
                role=AdminRole.owner,
                name="Owner",
            ))

        await db.commit()
        print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
