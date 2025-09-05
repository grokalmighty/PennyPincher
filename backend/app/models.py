from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import relationship
from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    issuer = Column(String)
    network = Column(String)
    last4 = Column(String)
    product_id = Column(String)
    user = relationship("User")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    posted_at = Column(Date)
    amount = Column(Float)
    currency = Column(String)
    merchant_norm = Column(String)
    mcc = Column(String, nullable=True)
    preset_category = Column(String)
    user_category = Column(String, nullable=True)
    classification_source = Column(String, nullable=True)

class Budget(Base):
    __tablename__ = "budgets"
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
    __tablename__ = "user_categories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    name = Column(String)
    parent_preset = Column(String)

class MerchantRule(Base):
    __tablename__= "merchant_rules"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    pattern = Column(String, nullable=False)
    user_category = Column(String, nullable=False)
    parent_preset = Column(String, nullable=False)
    priority = Column(Integer, default=100)

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(Date, nullable=True)
    priority = Column(Integer, default=1)
    active = Column(Boolean, default=True)

class TxnOverride(Base):
    __tablename__ = "txn_overrides"
    txn_id = Column(Integer, ForeignKey("transactions.id"), primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    category = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class CompanyRule(Base):
    __tablename__ = "company_rules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    company = Column(String, nullable=False)
    category = Column(String, nullable=False)
    priority = Column(Integer, default=100)
    __table_args__ = (UniqueConstraint("user_id", "company", name="uix_user_company"),)
    
class PlannedContribution(Base):
    __tablename__ = "planned_contributions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    month = Column(String, nullable=False) 
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (UniqueConstraint("user_id", "month", "goal_id", name="uix_user_month_goal"),)