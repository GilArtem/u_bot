from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, ARRAY, BigInteger, ForeignKey, Numeric, JSON, Date, Float
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs

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
    menu = Column(String)
    
    transactions = relationship("Transaction", back_populates='event')
    users = relationship("UserXEvent", back_populates='event')


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
async_session = async_sessionmaker(engine)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
