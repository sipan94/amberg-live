from math import ceil


class ListPagination:
    """Paginate a Python list with the same attributes as Flask-SQLAlchemy's Pagination,
    so both work with the same template macro. Needed for expanded recurring events."""

    def __init__(self, items: list, page: int, per_page: int):
        self.total = len(items)
        self.per_page = per_page
        self.pages = max(1, ceil(self.total / per_page))
        self.page = min(max(1, page), self.pages)
        start = (self.page - 1) * per_page
        self.items = items[start:start + per_page]

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def prev_num(self) -> int | None:
        return self.page - 1 if self.has_prev else None

    @property
    def next_num(self) -> int | None:
        return self.page + 1 if self.has_next else None
