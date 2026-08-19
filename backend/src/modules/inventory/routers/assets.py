"""
FastAPI routers for Fixed Assets and Depreciation.

Endpoints for:
- Fixed Asset CRUD
- Asset Depreciation Batch Processing
- Depreciation Reports
- Asset Disposal
"""

import logging
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError, ValidationError
from src.core.response import APIResponse
from src.modules.inventory.schemas.inventory import (
    CreateFixedAssetRequest,
    FixedAssetResponse,
    FixedAssetDetailResponse,
    DepreciationEntryResponse,
    RunDepreciationRequest,
    RunDepreciationResponse,
    AssetSummaryResponse,
)
from src.modules.inventory.services.asset_service import AssetService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["Fixed Assets & Depreciation"])


# ============================================================================
# FIXED ASSET CRUD
# ============================================================================


@router.post("/create", response_model=APIResponse)
async def create_fixed_asset(
    request: CreateFixedAssetRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create fixed asset."""
    try:
        service = AssetService(db)
        result = await service.create_asset(
            school_id=school_id,
            asset_number=request.asset_number,
            asset_name=request.asset_name,
            asset_category=request.asset_category,
            purchase_cost=request.purchase_cost,
            purchase_date=request.purchase_date,
            useful_life_years=request.useful_life_years,
            asset_description=request.asset_description,
            depreciation_method=request.depreciation_method,
            salvage_value=request.salvage_value,
            location=request.location,
            asset_manager_staff_id=request.asset_manager_staff_id,
        )
        
        return APIResponse.success(
            data=result,
            message="Fixed asset created",
            status_code=201,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Asset creation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error creating asset: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create asset",
            status_code=500,
        )


@router.get("/{asset_id}", response_model=APIResponse)
async def get_fixed_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get fixed asset detail."""
    try:
        service = AssetService(db)
        result = await service.get_asset(school_id, asset_id)
        
        return APIResponse.success(
            data=result,
            message="Asset retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Asset not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving asset: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve asset",
            status_code=500,
        )


@router.get("", response_model=APIResponse)
async def list_fixed_assets(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    status: str = Query(None),
    category: str = Query(None),
) -> APIResponse:
    """List fixed assets."""
    try:
        service = AssetService(db)
        assets = await service.list_assets(
            school_id,
            asset_status=status,
            asset_category=category,
        )
        
        return APIResponse.success(
            data=assets,
            message=f"Found {len(assets)} assets",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error listing assets: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list assets",
            status_code=500,
        )


# ============================================================================
# DEPRECIATION
# ============================================================================


@router.post("/depreciation/run-monthly", response_model=APIResponse)
async def run_monthly_depreciation(
    request: RunDepreciationRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL: Run monthly depreciation batch process.
    
    ALGORITHM:
    1. Query all active fixed assets
    2. For each asset: Calculate straight-line depreciation
    3. Create depreciation entries
    4. Post GL entries (DR Depreciation Expense, CR Accumulated Depreciation)
    5. Update asset accumulated depreciation
    
    Idempotent: If depreciation already run for month/year, skips.
    """
    try:
        service = AssetService(db)
        result = await service.run_monthly_depreciation(
            school_id=school_id,
            depreciation_month=request.depreciation_month,
            depreciation_year=request.depreciation_year,
        )
        
        return APIResponse.success(
            data=result,
            message="Monthly depreciation completed",
            status_code=200,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Depreciation run failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error running depreciation: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to run depreciation",
            status_code=500,
        )


@router.get("/{asset_id}/depreciation-history", response_model=APIResponse)
async def get_depreciation_history(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get depreciation history for asset."""
    try:
        service = AssetService(db)
        entries = await service.get_depreciation_entries(school_id, asset_id)
        
        return APIResponse.success(
            data=entries,
            message=f"Found {len(entries)} depreciation entries",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving depreciation history: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve history",
            status_code=500,
        )


# ============================================================================
# ASSET DISPOSAL
# ============================================================================


@router.post("/{asset_id}/dispose", response_model=APIResponse)
async def dispose_asset(
    asset_id: UUID,
    disposal_date: date = Query(...),
    disposal_reason: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Dispose of fixed asset."""
    try:
        service = AssetService(db)
        result = await service.dispose_asset(
            school_id=school_id,
            asset_id=asset_id,
            disposal_date=disposal_date,
            disposal_reason=disposal_reason,
        )
        
        return APIResponse.success(
            data=result,
            message="Asset disposed",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Asset not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error disposing asset: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to dispose asset",
            status_code=500,
        )


# ============================================================================
# ASSET SUMMARY & REPORTS
# ============================================================================


@router.get("/summary/all", response_model=APIResponse)
async def get_asset_summary(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get fixed assets summary."""
    try:
        service = AssetService(db)
        summary = await service.get_asset_summary(school_id)
        
        return APIResponse.success(
            data=summary,
            message="Asset summary retrieved",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error getting asset summary: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to get summary",
            status_code=500,
        )
