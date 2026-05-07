import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, EmailStr, Field, TypeAdapter, field_validator

logger = logging.getLogger(__name__)


class MessageCreate(BaseModel):
    to: list[EmailStr]
    cc: list[EmailStr] = []
    subject: str = Field(..., max_length=1024)
    body: str
    attachments: dict[str, str] = Field(default_factory=dict)

    @field_validator("to", "cc", mode="before")
    @classmethod
    def _normalize_email(cls, email: str) -> list[EmailStr]:
        return parse_email_list(email)


class Message(MessageCreate):
    id: str
    sender: EmailStr
    sent_at: datetime
    folder: str = "Inbox"
    read: bool = False


class Folder(BaseModel):
    id: str
    name: str


class EventCreate(BaseModel):
    subject: str
    start: datetime
    end: datetime
    body: str | None = None
    location: str | None = None
    attendees: list[EmailStr] = []


class Event(EventCreate):
    id: str
    organizer: EmailStr


class Contact(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: str | None = None
    manager: str | None = None  # Contact ID of the manager
    position: str | None = None


class UserProfile(BaseModel):
    manager: str | None = None  # Contact ID of the manager
    phone: str | None = None
    email: EmailStr | None = None
    position: str | None = None


BusySlot = tuple[datetime, datetime]
FreeSlot = tuple[datetime, datetime]


class Bucket(BaseModel):
    messages: list[Message] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    contacts: list[Contact] = Field(default_factory=list)
    folders: list[Folder] = Field(
        default_factory=lambda: [
            Folder(id="inbox", name="Inbox"),
            Folder(id="sent", name="Sent"),
        ]
    )
    profile: UserProfile = Field(default_factory=UserProfile)


class EmailSystemError(Exception):
    pass


# Utility helper
_email_list_adapter = TypeAdapter(list[EmailStr])


def parse_email_list(raw: str | list[str]) -> list[EmailStr]:
    if isinstance(raw, list):
        parts = raw
    else:
        parts = [p.strip() for p in re.split(r"[;,]", raw) if p.strip()]
    return _email_list_adapter.validate_python(parts)


class EmailSystem:

    def __init__(self) -> None:
        self._state: dict[str, Bucket] = {}
        self.default_user: str | None = None
        self.effects: list[dict[str, Any]] = []

    def initialize(self, config: dict[str, Any]):
        users_cfg = config.get("users")
        if not users_cfg:
            raise ValueError("Config must contain a non-empty 'users' mapping")
        # build a Bucket for each user in one go
        self._state = {u: Bucket(**v) for u, v in users_cfg.items()}
        self.default_user = next(iter(self._state))

    def _resolve_user(self, user: str | None) -> str:
        if user:
            return user
        if self.default_user:
            return self.default_user
        raise ValueError(
            "user must be provided when no default_user is set", self._state
        )

    def _bucket(self, user: str) -> Bucket:
        if user not in self._state:
            self._state[user] = Bucket()
        return self._state[user]

    def _record(self, op: str, user: str, **extra):
        self.effects.append(
            {
                "op": op,
                "user": user,
                **extra,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
        )

    # Mailbox
    def send_message(self, payload: MessageCreate, user: str | None = None) -> str:
        user = self._resolve_user(user)
        bucket = self._bucket(user)
        mid = str(uuid.uuid4())
        msg = Message(
            id=mid,
            sender=user,
            sent_at=datetime.now(timezone.utc),
            **payload.model_dump(),
        )
        bucket.messages.append(msg)
        self._record(
            "send_message",
            user,
            msg_id=mid,
            _from=user,
            to=payload.to,
            cc=payload.cc,
            subject=payload.subject,
            body=payload.body,
        )
        return mid

    def receive_message(
        self, payload: MessageCreate, sender: EmailStr, recipient: str | None = None
    ) -> str:
        recipient = self._resolve_user(recipient)
        bucket = self._bucket(recipient)
        mid = str(uuid.uuid4())
        msg = Message(
            id=mid,
            sender=sender,
            sent_at=datetime.now(timezone.utc),
            **payload.model_dump(),
        )
        bucket.messages.append(msg)
        self._record("receive_message", recipient, msg_id=mid, from_=sender)
        return mid

    def list_messages(
        self, folder: str = "Inbox", user: str | None = None
    ) -> list[Message]:
        user = self._resolve_user(user)
        msgs = [
            m for m in self._bucket(user).messages if m.folder.lower() == folder.lower()
        ]
        self._record("list_messages", user, folder=folder, count=len(msgs))
        return msgs

    def delete_message(
        self, message_id: str, folder: str | None = None, user: str | None = None
    ) -> bool:
        """Remove message; return True if deleted, else raise EmailSystemError."""
        user = self._resolve_user(user)
        bucket = self._bucket(user)
        msgs = bucket.messages
        before = len(bucket.messages)
        if folder:
            bucket.messages = [
                m
                for m in msgs
                if not (m.id == message_id and m.folder.lower() == folder.lower())
            ]
        else:
            bucket.messages = [m for m in msgs if m.id != message_id]

        if len(bucket.messages) < before:
            self._record(
                "delete_message", user, msg_id=message_id, folder=folder or "*"
            )
            return True
        raise EmailSystemError("message not found")

    # Calendar
    def create_event(self, payload: EventCreate, user: str | None = None) -> str:
        user = self._resolve_user(user)
        bucket = self._bucket(user)
        eid = str(uuid.uuid4())
        bucket.events.append(Event(id=eid, organizer=user, **payload.model_dump()))
        self._record("create_event", user, event_id=eid)
        return eid

    def list_events(self, user: str | None = None) -> list[Event]:
        user = self._resolve_user(user)
        ev = [e for e in self._bucket(user).events]
        self._record("list_events", user, count=len(ev))
        return ev

    def find_free_slots(
        self,
        start: datetime,
        end: datetime,
        slot_minutes: int = 30,
        user: str | None = None,
    ) -> list[FreeSlot]:
        user = self._resolve_user(user)
        ev = [e for e in self.list_events(user) if e.end > start and e.start < end]
        busy = sorted(
            ((max(e.start, start), min(e.end, end)) for e in ev), key=lambda t: t[0]
        )
        merged: list[BusySlot] = []
        for b in busy:
            if merged and b[0] <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], b[1]))
            else:
                merged.append(b)
        free: list[FreeSlot] = []
        cur = start
        delta = timedelta(minutes=slot_minutes)
        for b in merged:
            if b[0] - cur >= delta:
                free.append((cur, b[0]))
            cur = max(cur, b[1])
        if end - cur >= delta:
            free.append((cur, end))
        self._record(
            "find_free_slots",
            user,
            window=(start.isoformat(), end.isoformat()),
            count=len(free),
        )
        return free

    # Contacts
    def add_contact(
        self,
        name: str,
        email: EmailStr,
        phone: str | None = None,
        manager: str | None = None,
        position: str | None = None,
        user: str | None = None,
    ) -> str:
        """
        Add a new contact to the address book.

        Args:
            name: Contact's name
            email: Contact's email address
            phone: Contact's phone number (optional)
            manager: Contact ID of the manager (optional)
            position: Contact's job position (optional)
            user: User to add the contact for (optional)

        Returns:
            The contact ID of the newly created contact
        """
        user = self._resolve_user(user)
        cid = str(uuid.uuid4())

        self._bucket(user).contacts.append(
            Contact(
                id=cid,
                name=name,
                email=email,
                phone=phone,
                manager=manager,
                position=position,
            )
        )
        self._record(
            "add_contact",
            user,
            contact_id=cid,
            name=name,
            email=email,
            phone=phone,
            manager=manager,
            position=position,
        )
        return cid

    def list_contacts(self, user: str | None = None) -> list[Contact]:
        user = self._resolve_user(user)
        contacts = [c for c in self._bucket(user).contacts]
        self._record("list_contacts", user, count=len(contacts))
        return contacts

    def get_contact(self, contact_id: str, user: str | None = None) -> Contact:
        user = self._resolve_user(user)
        for contact in self._bucket(user).contacts:
            if contact.id == contact_id:
                self._record("get_contact", user, contact_id=contact_id)
                return contact
        raise EmailSystemError(f"Contact with id {contact_id} not found")

    # User Profile
    def get_user_profile(self, user: str | None = None) -> UserProfile:
        """Get the user's profile information."""
        user = self._resolve_user(user)
        profile = self._bucket(user).profile
        self._record("get_user_profile", user)
        return profile

    def update_user_profile(
        self, profile: UserProfile, user: str | None = None
    ) -> None:
        """Update the user's profile information."""
        user = self._resolve_user(user)
        bucket = self._bucket(user)
        bucket.profile = profile
        self._record("update_user_profile", user)

    def get_user_manager(self, user: str | None = None) -> Contact | None:
        """Get the user's manager contact, if any."""
        user = self._resolve_user(user)
        profile = self.get_user_profile(user)
        if profile.manager:
            try:
                return self.get_contact(profile.manager, user)
            except EmailSystemError:
                return None
        return None

    def get_manager_of_manager(self, user: str | None = None) -> Contact | None:
        """Get the manager of the user's manager, if any."""
        user = self._resolve_user(user)
        manager = self.get_user_manager(user)
        if manager and manager.manager:
            try:
                return self.get_contact(manager.manager, user)
            except EmailSystemError:
                return None
        return None
