"""Script to patch database.py with FeasibilityCheckRecord."""
import re

content = open('backend/app/database.py', 'r', encoding='utf-8').read()

new_block = (
    "\n\nclass FeasibilityCheckRecord(Base):\n"
    '    __tablename__ = "feasibility_checks"\n'
    "\n"
    "    check_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)\n"
    "    location: Mapped[str] = mapped_column(String(300), nullable=False)\n"
    "    status: Mapped[str] = mapped_column(String(30), nullable=False)\n"
    "    reason: Mapped[str] = mapped_column(String(500), nullable=False)\n"
    "    scheduling_available: Mapped[bool] = mapped_column(Boolean, nullable=False)\n"
    "    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))\n"
    "    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)\n"
    "    applicant_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)\n"
    "\n\n"
)

insert_before = 'def create_session_factory'
idx = content.find(insert_before)
if idx == -1:
    print("ERROR: could not find insert point")
else:
    new_content = content[:idx] + new_block + content[idx:]
    open('backend/app/database.py', 'w', encoding='utf-8', newline='\n').write(new_content)
    print('Done - FeasibilityCheckRecord inserted')
