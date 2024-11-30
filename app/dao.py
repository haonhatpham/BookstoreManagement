from app.models import Category, Book, User, Review
from app import app, db
from flask import request, jsonify
import hashlib
import cloudinary.uploader
from sqlalchemy import desc

def load_banner():
    books_banner = Book.query.limit(4).all()
    return books_banner

def load_feature_book():
    feature_book =  Book.query.offset(4).limit(6).all()
    return feature_book


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

def rate_product():
    data = request.json
    product_id = data.get("book_id")
    rating_value = data.get("rating")
    if not (1<= rating_value <=5):
        return jsonify({'error': 'Invalid rating value'}), 400
    new_rating = Review(book_id=product_id, rating=rating_value)
    db.session.add(new_rating)
    db.session.commit()
    return jsonify({'message': 'Rating submitted successfully!'})

def average_rating(book_id):
    ratings = Review.query.filter_by(product_id=book_id).all()
    if not ratings:
        return jsonify({'average_rating': 0})
    avg_rating = sum(r.rating for r in ratings) / len(ratings)
    return jsonify({'average_rating': avg_rating})