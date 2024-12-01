from flask_sqlalchemy.session import Session

from app.models import Category, Book, User, book_category
from app import app, db
import hashlib
import cloudinary.uploader
from sqlalchemy import desc, engine
from sqlalchemy.orm import session, sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

def load_banner():
    books_banner = Book.query.limit(4).all()
    return books_banner


def load_feature_book():
    feature_book =  Book.query.offset(4).limit(6).all()
    return feature_book

def load_book(book_id):
    return Book.query.filter(Book.id == book_id)

def load_related_book(category_ids):
    if isinstance(category_ids, str):
        category_ids = list(map(int, category_ids.split(',')))
    return (
        Book.query
        .join(book_category)
        .filter(book_category.c.category_id.in_(category_ids))
        .all()
    )

def load_category_ids():
    category_ids = db.session.query(Category.id).all()
    return [id[0] for id in category_ids]

def load_categories():
    return Category.query.order_by('id').limit(8).all()

def load_new_products(kw=None, cate_id=None, page=1):
    query = Book.query.order_by(desc(Book.id))
    if kw:
        query = query.filter(Book.name.contains(kw))
    if cate_id:
        query = query.filter(Book.category_id == cate_id)
    page_size = app.config["PAGE_SIZE"]
    start = (page - 1) * page_size
    query = query.slice(start, start + page_size)

    return query.all()

def count_products():
    return Book.query.count()

def add_user(name, username, password, avatar):
    pass


def auth_user(username, password):
    pass

def get_user_by_id(id):
    pass
