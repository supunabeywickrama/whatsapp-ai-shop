"""LLM tool registry. The model is grounded in real shop data through these
tools — it cannot quote prices, stock, or specs that don't come from a tool
result. Tool schemas are sent to the Anthropic API; execute() runs them."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Brand, Category, Product, ProductCondition
from app.models.marketing import Discount, DiscountType


TOOL_SCHEMAS: list[dict] = [
    {
        "name": "search_products",
        "description": "Search the shop inventory. Use whenever the customer asks about a product, brand, category, or price range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":     {"type": "string"},
                "category":  {"type": "string"},
                "brand":     {"type": "string"},
                "condition": {"type": "string", "enum": ["new", "used", "refurbished"]},
                "max_price": {"type": "number"},
                "limit":     {"type": "integer", "default": 5},
            },
        },
    },
    {
        "name": "get_product",
        "description": "Fetch full details of one product by id.",
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
    {
        "name": "apply_discount",
        "description": "Validate a discount code against a product and return the discounted price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code":       {"type": "string"},
                "product_id": {"type": "string"},
            },
            "required": ["code", "product_id"],
        },
    },
    {
        "name": "start_human_handoff",
        "description": "Escalate this conversation to a human agent. Call when the customer asks for a person, makes a complaint, or you cannot answer.",
        "input_schema": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    },
    {
        "name": "end_conversation",
        "description": "End the current chat cleanly. Call when the customer says goodbye, thanks, or stops engaging.",
        "input_schema": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    },
]


async def execute(db: AsyncSession, name: str, args: dict, ctx: dict) -> Any:
    if name == "search_products":     return await _search_products(db, args)
    if name == "get_product":         return await _get_product(db, args)
    if name == "apply_discount":      return await _apply_discount(db, args)
    if name == "start_human_handoff":
        ctx["handoff"] = args.get("reason", "agent_requested")
        return {"ok": True}
    if name == "end_conversation":
        ctx["end"] = args.get("reason", "goodbye")
        return {"ok": True}
    return {"error": f"unknown tool {name}"}


async def _search_products(db: AsyncSession, args: dict) -> list[dict]:
    stmt = select(Product).where(Product.is_active.is_(True))

    if cond := args.get("condition"):
        stmt = stmt.where(Product.condition == ProductCondition(cond))
    if mp := args.get("max_price"):
        stmt = stmt.where(Product.price <= mp)
    if cat := args.get("category"):
        stmt = stmt.join(Category).where(Category.name.ilike(cat))
    if br := args.get("brand"):
        stmt = stmt.join(Brand).where(Brand.name.ilike(br))
    if q := args.get("query"):
        stmt = stmt.where(Product.title.ilike(f"%{q}%"))

    stmt = stmt.limit(min(int(args.get("limit", 5)), 10))

    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [_serialize_product(p) for p in rows]


async def _get_product(db: AsyncSession, args: dict) -> dict:
    res = await db.execute(select(Product).where(Product.id == args["id"]))
    p = res.scalar_one_or_none()
    return _serialize_product(p, full=True) if p else {"error": "not_found"}


async def _apply_discount(db: AsyncSession, args: dict) -> dict:
    code = args["code"]
    product_id = args["product_id"]

    d_res = await db.execute(select(Discount).where(Discount.code == code))
    d = d_res.scalar_one_or_none()
    p_res = await db.execute(select(Product).where(Product.id == product_id))
    p = p_res.scalar_one_or_none()

    if not d or not d.is_active:
        return {"error": "invalid_code"}
    if d.ends_at < datetime.now(tz=timezone.utc):
        return {"error": "expired"}
    if d.max_uses is not None and d.used_count >= d.max_uses:
        return {"error": "exhausted"}
    if not p:
        return {"error": "product_not_found"}

    base = float(p.price)
    if d.type == DiscountType.percent:
        final = max(0.0, base * (1 - float(d.value) / 100))
    else:
        final = max(0.0, base - float(d.value))
    return {"code": code, "original_price": base, "final_price": round(final, 2)}


def _serialize_product(p: Product, full: bool = False) -> dict:
    out = {
        "id": p.id,
        "sku": p.sku,
        "title": p.title,
        "price": float(p.price),
        "discounted_price": float(p.discounted_price) if p.discounted_price else None,
        "stock": p.stock_qty,
        "condition": p.condition.value,
    }
    if full:
        out.update({
            "description": p.description,
            "specs": p.specs,
            "images": p.images,
        })
    return out
