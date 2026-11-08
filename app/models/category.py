from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    icon: Mapped[str] = mapped_column(String(40), default="other")  # key of a self-hosted SVG icon
    color: Mapped[str] = mapped_column(String(7), default="#64748b")  # hex, used for chips/markers
    sort_order: Mapped[int] = mapped_column(default=0)

    events: Mapped[list["Event"]] = relationship(back_populates="category")  # noqa: F821

    def slug_source(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Category {self.slug}>"
