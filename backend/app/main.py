from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.api import (
    auth,
    products,
    categories,
    brands,
    customers,
    conversations,
    discounts,
    broadcasts,
    ai,
    webhook,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Backend starting on :{settings.BACKEND_PORT} ({settings.NODE_ENV})")
    yield
    logger.info("Backend shutting down")


app = FastAPI(
    title="WhatsApp AI Shop Backend",
    version="0.1.0",
    description="Backend API for the WhatsApp AI Automation System (Mobile Shop)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health():
    return {"ok": True}


# Webhook is mounted at root path (Meta requires a fixed verify URL).
app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])

app.include_router(auth.router,          prefix="/api/auth",          tags=["auth"])
app.include_router(products.router,      prefix="/api/products",      tags=["products"])
app.include_router(categories.router,    prefix="/api/categories",    tags=["categories"])
app.include_router(brands.router,        prefix="/api/brands",        tags=["brands"])
app.include_router(customers.router,     prefix="/api/customers",     tags=["customers"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(discounts.router,     prefix="/api/discounts",     tags=["discounts"])
app.include_router(broadcasts.router,    prefix="/api/broadcasts",    tags=["broadcasts"])
app.include_router(ai.router,            prefix="/api/ai",            tags=["ai"])
