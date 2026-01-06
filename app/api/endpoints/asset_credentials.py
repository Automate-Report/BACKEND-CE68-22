from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.schemas.asset_credential import AssetCredentialCreate, AssetCredentialResponse
from app.services.asset_credential import asset_credential_service

router = APIRouter()

# GET credentials/credential_id
@router.get("/{credential_id}", response_model=AssetCredentialResponse)
async def get_credential_by_id(credential_id: int):
    credential = asset_credential_service.get_credential_by_id(credential_id)

    if not credential:
        HTTPException(status_code=404, detail="Credential not found")
    
    return credential

# GET 
@router.get("/byAsset/{asset_id}", response_model=AssetCredentialResponse)
async def get_credential_by_asset(asset_id: int):
    credential = asset_credential_service.get_credential_by_asset_id(asset_id)

    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    return credential

# POST (Create) credentials/
@router.post("/", response_model=AssetCredentialResponse)
async def create_credential(credential_in: AssetCredentialCreate):
    new_credential = asset_credential_service.create_credential(credential_in)

    return new_credential

# PUT (Update) credentials/credential_id
@router.put("/{credential_id}", response_model=AssetCredentialResponse)
async def update_credential(credential_id: int, credential_in: AssetCredentialCreate):
    credential = asset_credential_service.update_credential(
        credential_id=credential_id,
        credential_in=credential_in
    )

    if not credential:
        HTTPException(status_code=404, detail="Credential not found")
    
    return credential

# DELETE credentials/credential_id
@router.delete("/{credential_id}")
async def delete_credential(credential_id: int):
    success = asset_credential_service.delete_credential(credential_id)

    if not success:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"detail": "Project deleted successfully"}