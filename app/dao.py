# from app.models import Category, Product, User
from app import app, db
import hashlib
import cloudinary.uploader


def load_categories():
    pass

def load_products(kw=None, cate_id=None, page=1):
    pass

def add_user(name, username, password, avatar):
    pass

def auth_user(username, password):
    pass

def get_user_by_id(id):
    pass