from app.models import Category, Book, User, Role
from app import app, db
import hashlib
import cloudinary.uploader
from sqlalchemy import desc


def load_banner():
    books_banner = Book.query.limit(4).all()
    return books_banner


def load_feature_book():
    feature_book = Book.query.offset(4).limit(6).all()

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


def add_user(name, username, password, email, phone, birth, gender, avatar):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
    user_role = Role.query.filter_by(name="User").first()
    name_parts = name.strip().split(" ", 1)
    if len(name_parts) > 1:
        first_name = name_parts[1]
        last_name = name_parts[0]
    else:
        # Nếu không có dấu cách, mặc định đặt last_name là name và first_name rỗng
        first_name = ''
        last_name = name_parts[0]
    u = User(
        first_name=first_name,
        last_name=last_name,
        username=username.strip(),
        password=password,
        email=email.strip(),
        phone=phone.strip(),
        birth=birth,
        gender=gender,  # Nam active=True,
        role_id=user_role.id
    )

    if avatar:
        res = cloudinary.uploader.upload(avatar)
        print(res)
        u.avatar_file = res.get("secure_url")

    db.session.add(u)
    db.session.commit()


def auth_user(username, password):
    password = hashlib.md5(password.encode('utf-8')).hexdigest()

    return User.query.filter(User.username.__eq__(username.strip()),
                             User.password.__eq__(password)).first()


def get_user_by_id(id):
    return User.query.get(id)
