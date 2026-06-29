from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import SessionDep, get_current_user
from app.schemas.catalog import (
    BrandData,
    CatalogProductsResponse,
    CategoryData,
    ProductData,
    RegionData,
    ResponseMeta,
)
from app.schemas.response import ApiResponse
from app.services.catalog import CatalogService

router = APIRouter(
    prefix="/catalog",
    tags=["Catalog"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/regions", response_model=ApiResponse[list[RegionData]])
async def list_regions(session: SessionDep) -> ApiResponse[list[RegionData]]:
    regions, total_count = await CatalogService(session).regions()
    return ApiResponse(
        message="Regions retrieved",
        total_count=total_count,
        data=regions,
    )


@router.get("/categories", response_model=ApiResponse[list[CategoryData]])
async def list_categories(session: SessionDep) -> ApiResponse[list[CategoryData]]:
    return ApiResponse(
        message="Categories retrieved", data=await CatalogService(session).categories()
    )


@router.get("/brands", response_model=ApiResponse[list[BrandData]])
async def list_brands(
    session: SessionDep,
    region_id: int | None = None,
) -> ApiResponse[list[BrandData]]:
    return ApiResponse(
        message="Brands retrieved", data=await CatalogService(session).brands(region_id=region_id)
    )


@router.get("/products", response_model=CatalogProductsResponse)
async def list_products(
    session: SessionDep,
    region_id: int | None = None,
    category_id: int | None = None,
    brand_id: int | None = None,
    search: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> CatalogProductsResponse:
    data = await CatalogService(session).products(
        region_id=region_id,
        category_id=category_id,
        brand_id=brand_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return CatalogProductsResponse(
        message="Products retrieved successfully.",
        data=data,
        meta=ResponseMeta(
            timestamp=datetime.now(timezone.utc),
            request_id=f"req_{uuid4().hex[:16]}",
        ),
    )


@router.get("/products/{product_id}", response_model=ApiResponse[ProductData])
async def get_product(product_id: int, session: SessionDep) -> ApiResponse[ProductData]:
    return ApiResponse(
        message="Product retrieved", data=await CatalogService(session).product(product_id)
    )
