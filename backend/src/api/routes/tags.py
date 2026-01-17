from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from src.api.deps import get_session
from src.schemas.advanced import TagCreate, TagRead, TagUpdate
from src.services.tag_service import TagService

router = APIRouter()


@router.post("", response_model=TagRead, status_code=201)
def create_tag(tag_in: TagCreate, session: Session = Depends(get_session)):
    service = TagService(session)
    try:
        tag = service.create_tag(tag_in)
        return tag
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[TagRead])
def list_tags(session: Session = Depends(get_session)):
    service = TagService(session)
    return service.list_tags()


@router.put("/{tag_id}", response_model=TagRead)
def update_tag(tag_id: UUID, tag_in: TagUpdate, session: Session = Depends(get_session)):
    service = TagService(session)
    try:
        tag = service.update_tag(tag_id, tag_in)
        return tag
    except ValueError as e:
        # Assuming ValueError means not found or duplicate
        # We need to distinguish for correct status code, but for now 404/400
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: UUID, session: Session = Depends(get_session)):
    service = TagService(session)
    success = service.delete_tag(tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return
