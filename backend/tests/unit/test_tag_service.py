import uuid

import pytest
from sqlmodel import Session

from src.models.advanced import Tag
from src.schemas.advanced import TagCreate, TagUpdate
from src.services.tag_service import TagService


class TestTagService:
    def test_create_tag(self, session: Session):
        service = TagService(session)
        tag_create = TagCreate(name="Vacation", color="#FF5733")
        tag = service.create_tag(tag_create)

        assert tag.id is not None
        assert tag.name == "Vacation"
        assert tag.color == "#FF5733"

        # Verify db persistence
        saved_tag = session.get(Tag, tag.id)
        assert saved_tag is not None
        assert saved_tag.name == "Vacation"

    def test_create_duplicate_tag_fails(self, session: Session):
        service = TagService(session)
        service.create_tag(TagCreate(name="Duplicate"))

        with pytest.raises(ValueError):  # Specific exception to be defined
            service.create_tag(TagCreate(name="Duplicate"))

    def test_list_tags(self, session: Session):
        service = TagService(session)
        service.create_tag(TagCreate(name="Tag1"))
        service.create_tag(TagCreate(name="Tag2"))

        tags = service.list_tags()
        assert len(tags) == 2
        names = {t.name for t in tags}
        assert "Tag1" in names
        assert "Tag2" in names

    def test_get_tag(self, session: Session):
        service = TagService(session)
        created = service.create_tag(TagCreate(name="Target"))

        fetched = service.get_tag(created.id)
        assert fetched is not None
        assert fetched.id == created.id

        missing = service.get_tag(uuid.uuid4())
        assert missing is None

    def test_update_tag(self, session: Session):
        service = TagService(session)
        tag = service.create_tag(TagCreate(name="OldName", color="Red"))

        updated = service.update_tag(tag.id, TagUpdate(name="NewName"))
        assert updated.name == "NewName"
        assert updated.color == "Red"

        fetched = service.get_tag(tag.id)
        assert fetched.name == "NewName"

    def test_delete_tag(self, session: Session):
        service = TagService(session)
        tag = service.create_tag(TagCreate(name="To Delete"))

        success = service.delete_tag(tag.id)
        assert success is True

        assert service.get_tag(tag.id) is None

        # Delete non-existent
        assert service.delete_tag(uuid.uuid4()) is False
