from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.schemas.credential import CredentialCreate, CredentialResponse
from app.services.credential import credential_service

router = APIRouter()

# GET credentials/credential_id
@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential_by_id(credential_id: int):
    credential = credential_service.get_credential_by_id(credential_id)

    if not credential:
        HTTPException(status_code=404, detail="Credential not found")
    
    return credential

# GET 
@router.get("/byAsset/{asset_id}", response_model=CredentialResponse | None)
async def get_credential_by_asset(asset_id: int):
    credential = credential_service.get_credential_by_id(asset_id)

    if not credential:
        HTTPException(status_code=404, detail="Credential not found")
    
    return credential

# POST (Create) credentials/
@router.post("/", response_model=CredentialResponse)
async def create_credential(credential_in: CredentialCreate):
    new_credential = credential_service.create_credential(credential_in)

    return new_credential

# PUT (Update) credentials/credential_id
@router.put("/{credential_id}", response_model=CredentialResponse)
async def update_credential(credential_id: int, credential_in: CredentialCreate):
    credential = credential_service.update_credential(
        credential_id=credential_id,
        credential_in=credential_in
    )

    if not credential:
        HTTPException(status_code=404, detail="Credential not found")
    
    return credential

# DELETE credentials/credential_id
@router.delete("/{credential_id}")
async def delete_credential(credential_id: int):
    success = credential_service.delete_credential(credential_id)

    if not success:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"detail": "Project deleted successfully"}