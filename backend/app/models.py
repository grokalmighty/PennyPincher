from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

class User(Base):
    __table__name = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)

class Account(Base):
    __table__name = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    issuer = Column(String)
    network = Column(String)
    last4 = Column(String)
    product_id = Column(String)
    user = relationship("User")

class Transaction(Base):
    __table__name = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    account_id = Column(Integer)
    posted_at = Column(Date)
    amount = Column(Float)
    currency = Column(String)
    merchant_norm = Column(String)
    mcc = Column(String, nullable=True)
    preset_category = Column(String)
    user_category = Column(String, nullable=True)

class Budget(Base):
    __table__ = "budgets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    month = Column(String)
    category = Column(String)
    limit_amount = Column(Float)
    priority = Column(String)

class MarketSignal(Base):
    __tablename__ = "market_signals"
    id = Column(Integer, primary_key=True, index=True)
    month = Column(String)
    category = Column(String)
    yoy = Column(Float)


class UserCategory(Base):
    __table__name = "user_categories"
    id = Column(Integer, index=True)
    name = Column(String)
    parent_preset = Column(String)

class MerchantRule(Base):
    __table__name = "merchant_rules"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    merchant_pattern = Column(String)
    user_category_id = Column(Integer, ForeignKey("user_categories.id"))