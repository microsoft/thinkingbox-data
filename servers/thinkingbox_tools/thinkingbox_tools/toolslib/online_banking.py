# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, field_serializer

DT_EPOCH = datetime.datetime(2024, 4, 1, 10, 10, 0, tzinfo=datetime.timezone.utc)


def parse_dt_utc(value):
    if isinstance(value, datetime.datetime):
        return value.astimezone(datetime.timezone.utc)
    return datetime.datetime.fromisoformat(value).replace(tzinfo=datetime.timezone.utc)


class Account(BaseModel):
    account_type: Literal["checking", "savings", "investment"]
    account_number: str
    balance: float = 0.0


class Payee(BaseModel):
    name: str
    account_number: str


class ScheduledBill(BaseModel):
    user_account: str
    payee_account: str
    amount: float
    date: Annotated[datetime.datetime, BeforeValidator(parse_dt_utc)]

    @field_serializer("date")
    def serialize_date(self, dt: datetime.datetime, _info):
        return dt.strftime("%Y-%m-%d")


class Transaction(BaseModel):
    transaction_type: Literal["transfer", "bill_payment"]
    from_account: str
    to_account: str
    amount: float
    timestamp: Annotated[datetime.datetime, BeforeValidator(parse_dt_utc)] = DT_EPOCH

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: datetime.datetime, _info):
        return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


class BankingSystemError(Exception):
    pass


class BankingSystem:
    def __init__(self):
        # Initialize accounts and payees lists
        self.accounts: dict[str, Account] = {}
        self.payees: dict[str, Payee] = {}
        self.transactions: list[Transaction] = []
        self.scheduled_bills: list[ScheduledBill] = []
        self.time = DT_EPOCH + datetime.timedelta(hours=30)

    def get_accounts(self) -> list[Account]:
        return list(self.accounts.values())

    def get_balance(self, account_number: str) -> float:
        acct = self.accounts.get(account_number)
        if not acct:
            raise BankingSystemError(f"Account not found: {account_number}")
        return acct.balance

    def transfer(self, from_account: str, to_account: str, amount: float) -> None:
        sender = self.accounts.get(from_account)
        receiver = self.accounts.get(to_account)
        if not sender or not receiver:
            raise BankingSystemError("Invalid account number(s)")
        if sender.balance < amount:
            raise BankingSystemError("Insufficient funds")
        now = datetime.datetime.now(datetime.timezone.utc)
        sender.balance -= amount
        receiver.balance += amount
        txn = Transaction(
            transaction_type="transfer",
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            timestamp=now,
        )
        self.transactions.append(txn)

    def deposit(self, account_number: str, amount: float) -> float:
        acct = self.accounts.get(account_number)
        if not acct:
            raise BankingSystemError(f"Account not found: {account_number}")
        acct.balance += amount
        return acct.balance

    def schedule_bill(
        self,
        user_account: str,
        payee_account: str,
        amount: float,
        date: datetime.datetime,
    ) -> ScheduledBill:
        acct = self.accounts.get(user_account)
        if not acct:
            raise BankingSystemError(f"Account not found: {user_account}")
        payee = self.payees.get(payee_account)
        if not payee:
            raise BankingSystemError(
                f"Payee not found: {payee_account} in {self.payees.keys()}"
            )
        sb = ScheduledBill(
            user_account=user_account,
            payee_account=payee.account_number,
            amount=amount,
            date=date,
        )
        self.scheduled_bills.append(sb)
        acct.balance -= amount
        return sb

    def get_payees(self) -> list[Payee]:
        return list(self.payees.values())
