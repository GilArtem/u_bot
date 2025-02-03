from sqlalchemy import Column, String, Boolean, BigInteger, ForeignKey, Date, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs, AsyncSession
from datetime import datetime
from instance import SQL_URL_RC


class Base(AsyncAttrs, DeclarativeBase):
    pass


class TransactionRequest(Base):
    """
    Класс, представляющий информацию о транзакциях.
    
    Атрибуты:
        id (BigInteger): Уникальный идентификатор транзакции. Первичный ключ.
        admin_id (BigInteger): Идентификатор администратора, создавшего запрос.
                              Внешний ключ, ссылается на таблицу `user`.
        user_id (BigInteger): Идентификатор пользователя, для которого создан запрос.
                             Внешний ключ, ссылается на таблицу `user`.
        event_id (BigInteger, optional): Идентификатор события, связанного с транзакцией.
                                        Внешний ключ, ссылается на таблицу `event`.
                                        Может быть `None`, если транзакция не связана с событием.
        amount (Float): Сумма транзакции.
        status (String): Статус транзакции. По умолчанию 'in_process'.
        operation_type (String): Тип операции ('debit' для списания, 'balance_up' для пополнения).
        created_at (DateTime): Дата и время создания транзакции. По умолчанию текущее время.

    Связи:
        admin (User): Связь с администратором, создавшим запрос.
                     Использует `admin_id` как внешний ключ.
        user (User): Связь с пользователем, для которого создан запрос.
                    Использует `user_id` как внешний ключ.
        event (Event): Связь с событием, связанным с транзакцией.
                      Использует `event_id` как внешний ключ.
    """
    __tablename__ = "transaction_request"
    
    id = Column(BigInteger, primary_key=True, index=True, nullable=False)
    admin_id = Column(BigInteger, ForeignKey("user.id"))
    user_id = Column(BigInteger, ForeignKey("user.id"))
    event_id = Column(BigInteger, ForeignKey("event.id"), nullable=True) 
    amount = Column(Float)
    status = Column(String, default='in_process') 
    operation_type = Column(String, nullable=False)        
    created_at = Column(DateTime, default=datetime.now)
    
    admin = relationship("User", foreign_keys=[admin_id], back_populates="admin_requests")
    user = relationship("User", foreign_keys=[user_id], back_populates="user_requests")
    event = relationship('Event', back_populates='transactions')


class User(Base):
    """
    Класс, представляющий информацию о пользователе/администраторе.
    
    Атрибуты:
        id (BigInteger): Уникальный идентификатор пользователя. Первичный ключ.
        name (String): Имя пользователя. По умолчанию пустая строка.
        balance (Float): Баланс пользователя. По умолчанию 0.0.
        is_superuser (Boolean): Флаг, указывающий, является ли пользователь администратором. По умолчанию False.

    Связи:
        events (list[UserXEvent]): Связь с таблицей `user_x_event`, представляющая события,
                                   связанные с пользователем.
        transactions (list[TransactionRequest]): Связь с таблицей `transaction_request`,
                                                 представляющая транзакции, созданные для пользователя.
        admin_requests (list[TransactionRequest]): Связь с таблицей `transaction_request`,
                                                   представляющая транзакции, созданные администратором.
        user_requests (list[TransactionRequest]): Связь с таблицей `transaction_request`,
                                                  представляющая транзакции, связанные с пользователем.
    """
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, index=True, nullable=False)
    name = Column(String, default='')
    balance = Column(Float, default=0.0)
    is_superuser = Column(Boolean, default=False)
    
    events = relationship('UserXEvent', back_populates='user')
    transactions = relationship("TransactionRequest", foreign_keys=[TransactionRequest.user_id], back_populates='user')
    admin_requests = relationship("TransactionRequest", foreign_keys=[TransactionRequest.admin_id], back_populates="admin")
    user_requests = relationship("TransactionRequest", foreign_keys=[TransactionRequest.user_id], back_populates="user")


class Event(Base):
    """
    Класс, представляющий информацию о событиях (ивентах).
     
    Атрибуты:
        id (BigInteger): Уникальный идентификатор события. Первичный ключ.
        title (String): Название события. Должно быть уникальным.
        date (Date): Дата проведения события.
        description (String): Описание события.
        menu_id (BigInteger, optional): Идентификатор меню, связанного с событием.
                                        Внешний ключ, ссылается на таблицу `menu`.
                                        Может быть `None`.

    Связи:
        transactions (list[TransactionRequest]): Связь с таблицей `transaction_request`,
                                                 представляющая транзакции, связанные с событием.
        users (list[UserXEvent]): Связь с таблицей `user_x_event`, представляющая пользователей,
                                  связанных с событием.
        menu (Menu): Связь с таблицей `menu`, представляющая меню, связанное с событием.
    """
    __tablename__ = "event"
    
    id = Column(BigInteger, primary_key=True, index=True, nullable=False)
    title = Column(String, unique=True)
    date = Column(Date)
    description = Column(String)
    menu_id = Column(BigInteger, ForeignKey("menu.id"), nullable=True) 
    
    transactions = relationship("TransactionRequest", back_populates='event')
    users = relationship("UserXEvent", back_populates='event')
    menu = relationship("Menu", back_populates="events")


class Menu(Base):
    """
    Класс, представляющий информацию о меню.
     
    Атрибуты:
        id (BigInteger): Уникальный идентификатор меню. Первичный ключ.
        title (String): Название меню.
        price (Float): Цена меню.
        picture_path (String, optional): Путь к изображению меню. Может быть `None`.

    Связи:
        events (list[Event]): Связь с таблицей `event`, представляющая события,
                              связанные с данным меню.
    """
    __tablename__ = "menu"
    
    id = Column(BigInteger, primary_key=True, index=True, nullable=False, autoincrement=True)
    title = Column(String)
    price = Column(Float)
    picture_path = Column(String, nullable=True)
    
    events = relationship("Event", back_populates="menu")


class UserXEvent(Base):
    """
    Класс, представляющий связь между пользователями и событиями.

    Атрибуты:
        user_id (BigInteger): Идентификатор пользователя. Первичный ключ.
                              Внешний ключ, ссылается на таблицу `user`.
        event_id (BigInteger): Идентификатор события. Первичный ключ.
                               Внешний ключ, ссылается на таблицу `event`.

    Связи:
        user (User): Связь с таблицей `user`, представляющая пользователя,
                     связанного с данным событием.
        event (Event): Связь с таблицей `event`, представляющая событие,
                       связанное с данным пользователем.
    """
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