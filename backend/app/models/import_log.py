"""資料匯入紀錄(doc/data-model.md 2.10):何時、從哪個來源、哪個遊戲版本。"""

from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ImportLog(Base):
    __tablename__ = "import_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    imported_at: Mapped[datetime]
    source: Mapped[str] = mapped_column(String(200))
    game_version: Mapped[str | None] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(Text)
