from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import DateTime, Integer, String, Text, Boolean, Float, ForeignKey, create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class QuoteRecord(Base):
    __tablename__ = "quotes"

    quote_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    pricing_version: Mapped[str] = mapped_column(String(50), nullable=False)
    profile_json: Mapped[str] = mapped_column(Text, nullable=False)
    items_json: Mapped[str] = mapped_column(Text, nullable=False)
    monthly_total_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    setup_total_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)


class QuoteItemRecord(Base):
    __tablename__ = "quote_items"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quote_id: Mapped[str] = mapped_column(ForeignKey("quotes.quote_id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    monthly_price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    setup_price_minor: Mapped[int] = mapped_column(Integer, nullable=False)


class ConversationRecord(Base):
    __tablename__ = "conversations"

    conversation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    lead_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("leads.lead_id"), nullable=True, index=True)
    profile_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ConversationMessageRecord(Base):
    __tablename__ = "conversation_messages"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.conversation_id"), index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ConsentRecord(Base):
    __tablename__ = "consents"

    consent_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    applicant_id: Mapped[str] = mapped_column(String(100), index=True)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    purpose: Mapped[str] = mapped_column(String(100), default="kyc", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class KycCaseRecord(Base):
    __tablename__ = "kyc_cases"

    applicant_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    reasons_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class KycAuditRecord(Base):
    __tablename__ = "kyc_audit_events"

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    applicant_id: Mapped[str] = mapped_column(String(100), index=True)
    event: Mapped[str] = mapped_column(String(80), nullable=False)
    detail_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class KycDocumentRecord(Base):
    __tablename__ = "kyc_documents"

    document_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    applicant_id: Mapped[str] = mapped_column(String(100), index=True)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str | None] = mapped_column(String(500))
    extracted_fields_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class OrderRecord(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    quote_id: Mapped[str] = mapped_column(ForeignKey("quotes.quote_id"), unique=True, index=True)
    applicant_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(30), default="NOT_STARTED", nullable=False)
    installation_status: Mapped[str] = mapped_column(String(30), default="NOT_SCHEDULED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class OrderEventRecord(Base):
    __tablename__ = "order_events"

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"), index=True)
    actor: Mapped[str] = mapped_column(String(80), nullable=False)
    previous_state: Mapped[str] = mapped_column(String(40), nullable=False)
    new_state: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PaymentRecord(Base):
    __tablename__ = "payments"

    payment_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"), index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(100))
    reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class InstallationRecord(Base):
    __tablename__ = "installations"

    installation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"), unique=True)
    location: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(String(500))


class AssignmentRecord(Base):
    __tablename__ = "assignments"

    assignment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_type: Mapped[str] = mapped_column(String(40), nullable=False)
    case_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class HumanAssistanceRecord(Base):
    __tablename__ = "human_assistance_cases"

    case_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    applicant_id: Mapped[str | None] = mapped_column(String(100), index=True)
    lead_id: Mapped[str | None] = mapped_column(String(36), index=True)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class LeadRecord(Base):
    __tablename__ = "leads"

    lead_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    segment: Mapped[str] = mapped_column(String(80), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))




class FeasibilityCheckRecord(Base):
    __tablename__ = "feasibility_checks"

    check_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    scheduling_available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    applicant_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)


def create_session_factory(database_path: Path):
    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{database_path}", future=True)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        for table, column, definition in (
            ("leads", "archived_at", "DATETIME"),
            ("conversations", "lead_id", "VARCHAR(36)"),
        ):
            columns = {
                row[1]
                for row in connection.execute(text(f"PRAGMA table_info({table})"))
            }
            if column not in columns:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
    return sessionmaker(bind=engine, expire_on_commit=False)
