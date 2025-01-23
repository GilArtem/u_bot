from sqlalchemy import Column, String, Boolean, BigInteger, ForeignKey, Date, Float
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs, AsyncSession

from datetime import datetime

from instance import SQL_URL_RC

class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, index=True, nullable=False)
    name = Column(String, default='')
    balance = Column(Float, default=0.0)
    is_superuser = Column(Boolean, default=False)

    transactions = relationship("Transaction", back_populates='user')
    events = relationship('UserXEvent', back_populates='user')
    

class Event(Base):
    __tablename__ = "event"
    
    id = Column(BigInteger, primary_key=True, index=True, nullable=False)
    title = Column(String)
    date = Column(Date)
    description = Column(String)
    menu_id = Column(BigInteger, ForeignKey("menu.id"), nullable=True) 
    
    transactions = relationship("Transaction", back_populates='event')
    users = relationship("UserXEvent", back_populates='event')
    menu = relationship("Menu", back_populates="events")


class Menu(Base):
    __tablename__ = "menu"
    
    id = Column(BigInteger, primary_key=True, index=True, nullable=False)
    title = Column(String)
    price = Column(Float)
    picture_path = Column(String, nullable=True)
    
    events = relationship("Event", back_populates="menu")


class Transaction(Base):
    __tablename__ = "transaction"
    
    id = Column(BigInteger, primary_key=True, index=True, nullable=False)
    user_id = Column(BigInteger, ForeignKey("user.id"))
    event_id = Column(BigInteger, ForeignKey("event.id"), nullable=True) # При пополнении данные об ивенте не обязательны
    amount = Column(Float)
    date = Column(Date)
    type = Column(String)  # пополнение или списание

    user = relationship("User", back_populates='transactions')
    event = relationship('Event', back_populates='transactions')


class UserXEvent(Base):
    __tablename__ = "user_x_event"
    
    user_id = Column(BigInteger, ForeignKey('user.id'), primary_key=True)
    event_id = Column(BigInteger, ForeignKey('event.id'), primary_key=True)
    
    user = relationship("User", back_populates="events")
    event = relationship("Event", back_populates="users")


engine = create_async_engine(url=SQL_URL_RC, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class TransactionRequest(Base):
    __tablename__ = "transaction_request"
    
    id = Column(BigInteger, primary_key=True, index=True, nullable=False)
    admin_id = Column(BigInteger, ForeignKey("user.id"))
    user_id = Column(BigInteger, ForeignKey("user.id"))
    amount = Column(Float)
    status = Column(String, default='in_process')  # in_process, completed, expired
    created_at = Column(Date, default=datetime.now)
    
    admin = relationship("User", foreign_keys=[admin_id], back_populates="admin_requests")
    user = relationship("User", foreign_keys=[user_id], back_populates="user_requests")

User.admin_requests = relationship("TransactionRequest", foreign_keys=[TransactionRequest.admin_id], back_populates="admin")
User.user_requests = relationship("TransactionRequest", foreign_keys=[TransactionRequest.user_id], back_populates="user")