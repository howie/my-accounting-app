from uuid import UUID

from sqlmodel import Session, select

from src.models.advanced import Tag
from src.schemas.advanced import TagCreate, TagUpdate


class TagService:
    def __init__(self, session: Session):
        self.session = session

    def create_tag(self, tag_data: TagCreate) -> Tag:
        # Check for duplicates
        existing = self.session.exec(select(Tag).where(Tag.name == tag_data.name)).first()
        if existing:
            raise ValueError(f"Tag with name '{tag_data.name}' already exists.")

        tag = Tag.model_validate(tag_data)
        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)
        return tag

    def list_tags(self) -> list[Tag]:
        return list(self.session.exec(select(Tag)).all())

    def get_tag(self, tag_id: UUID) -> Tag | None:
        return self.session.get(Tag, tag_id)

    def update_tag(self, tag_id: UUID, tag_data: TagUpdate) -> Tag:
        tag = self.session.get(Tag, tag_id)
        if not tag:
            raise ValueError(f"Tag with id {tag_id} not found.")

        tag_data_dict = tag_data.model_dump(exclude_unset=True)

        # If updating name, check for duplicates
        if "name" in tag_data_dict:
            existing = self.session.exec(
                select(Tag).where(Tag.name == tag_data_dict["name"])
            ).first()
            if existing and existing.id != tag_id:
                raise ValueError(f"Tag with name '{tag_data_dict['name']}' already exists.")

        for key, value in tag_data_dict.items():
            setattr(tag, key, value)

        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)
        return tag

    def delete_tag(self, tag_id: UUID) -> bool:
        tag = self.session.get(Tag, tag_id)
        if not tag:
            return False
        self.session.delete(tag)
        self.session.commit()
        return True
