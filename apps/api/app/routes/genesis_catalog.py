from __future__ import annotations

from fastapi import APIRouter

from app.services.genesis_catalog.genesis_feature_catalog import get_genesis_feature_catalog

router = APIRouter(tags=["genesis-catalog"])


@router.get("/genesis/catalog")
def get_catalog() -> dict:
    return get_genesis_feature_catalog()
