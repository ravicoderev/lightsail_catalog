from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSON

import psycopg2

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(250), nullable=False)
    user_email = Column(String(250), nullable=False)
    user_picture = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'user_email': self.user_email            
        }

    def __init__(self, user_id, user_name, user_email, user_picture):
        self.user_id = user_id
        self.user_name = user_name
        self.user_email = user_email
        self.user_picture = user_picture


class Category(Base):
    __tablename__ = 'category'

    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    users = relationship(Users)

    # JSON Responses : Serialize function to be able to send JSON objects in a serializable format
    @property
    def serialize(self):
        """ Return object in serializable format """
        return{
            'category_id': self.category_id,
            'category_name': self.category_name
        }


    def __init__(self, category_id, category_name, user_id):
        self.category_id = category_id
        self.category_name = category_name
        self.user_id = user_id


class Items(Base):
    __tablename__ = 'items'

    item_id = Column(Integer, primary_key=True)
    item_name = Column(String(80), nullable=False)
    item_description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.category_id', ondelete='CASCADE'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    users = relationship(Users)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'item_id': self.item_id,
            'item_name': self.item_name,
            'item_description': self.item_description            
        }


    def __init__(self, item_id, item_name, item_description, category_id, user_id):
        self.item_id = item_id
        self.item_name = item_name
        self.item_description = item_description
        self.category_id = category_id
        self.user_id = user_id


# engine = create_engine('sqlite:///sportscatalogitems.db', connect_args={'check_same_thread': False})
# Create engine for Postgres
DBNAME = "sportscatalogitems"
USER="sportscatalogitems"
PASSWORD="1234"
HOST="localhost"
PORT="5432"

engine = create_engine('postgresql+psycopg2://sportscatalogitems:1234@localhost/sportscatalogitems')

Base.metadata.create_all(engine)
