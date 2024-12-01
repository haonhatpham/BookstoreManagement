from PIL.ImageChops import duplicate
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Boolean, Text, DECIMAL, DOUBLE, Enum
from sqlalchemy.orm import relationship, backref
from app import db, app
from enum import Enum as StatusEnum
from flask_login import RoleMixin, UserMixin
from sqlalchemy.sql import func
import hashlib
import json, random, os


class OrderEnum(StatusEnum):
    CHOXULY = 1
    DAXACNHAN = 2
    DAGIAO = 3
    DANGGIAOHANG = 4
    DAHUY = 5


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Role(BaseModel):
    __tablename__ = 'role'
    name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False, unique=True)
    description = Column(String(45, 'utf8mb4_unicode_ci'))

    permissions = relationship('Permission', secondary='role_has_permission', lazy='subquery',
                               backref=backref('roles', lazy=True))
    users = relationship('User', backref='role', lazy=True)


class Address(BaseModel):
    __tablename__ = 'address'
    city = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    district = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    ward = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    details = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)

    users = relationship("User", backref='Address', lazy=True)


class User(BaseModel):
    __tablename__ = 'user'
    first_name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    last_name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    email = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    phone = Column(String(11, 'utf8mb4_unicode_ci'))
    birth = Column(DateTime)
    gender = Column(Boolean, default=True)  # 1:nam 0:Nữ
    avatar_file = Column(String(100, 'utf8mb4_unicode_ci'), nullable=True)
    active = Column(Boolean, default=True)  # 1: còn hđ 0:hết hđ

    role_id = Column(ForeignKey(Role.id), nullable=False, index=True)
    address_id = Column(ForeignKey(Address.id), index=True)

    customer_orders = relationship("Order", backref="customer", lazy=True, foreign_keys='Order.customer_id')  # 1-n
    employee_orders = relationship("Order", backref="employee", lazy=True, foreign_keys='Order.employee_id')  # 1-n
    reviews = relationship('Review', backref='user', lazy=True)  # 1-n
    import_tickets = relationship('ImportTicket', backref='user', lazy=True)  # 1-n
    vouchers = db.relationship('Voucher', secondary='user_has_voucher', lazy='subquery',
                               backref=db.backref('users', lazy=True))  # n-n
    permission = db.relationship('Permission', secondary='user_has_permission', lazy='subquery',
                                 backref=backref('users', lazy=True))  # n-n
    wish_list_book = relationship('Book', secondary='wish_list_book', lazy='subquery',
                                  backref=backref('users', lazy=True))


class BankingInformation(BaseModel):
    __tablename__ = 'banking_information'
    vnpay_code = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    card_type = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    bank_code = Column(String(20, 'utf8mb4_unicode_ci'), nullable=False)
    payment_status = Column(Boolean, nullable=False, default=True)

    order = relationship('Order', backref='banking_information', lazy=True, uselist=False)


class Order(BaseModel):
    __tablename__ = 'order'
    customer_id = Column(ForeignKey(User.id), index=True, nullable=False)
    employee_id = Column(ForeignKey(User.id), index=True, nullable=False)
    initiated_date = Column(DateTime, nullable=False)
    cancel_date = Column(DateTime, nullable=False)
    paid_date = Column(DateTime, nullable=True)
    delivered_date = Column(DateTime, nullable=True, default=None)
    status = Column(Enum(OrderEnum), default=OrderEnum.CHOXULY)
    payment_method_id = Column(ForeignKey('payment_method.id'), index=True, nullable=False)
    banking_information_id = Column(ForeignKey(BankingInformation.id), unique=True, nullable=True)  # 1-1

    books = relationship('OrderDetail', backref='order')


class Author(BaseModel):
    __tablename__ = 'author'

    first_name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    last_name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)


class WishListBook(BaseModel):
    __tablename__ = 'wish_list_book'
    user_id = Column(ForeignKey('user.id'), nullable=False, index=True)
    book_id = Column(ForeignKey('book.id'), nullable=False, index=True)


class Category(BaseModel):
    __tablename__ = 'category'
    name = Column(String(200, 'utf8mb4_unicode_ci'), nullable=False, unique=True)
    image= Column(String(200, 'utf8mb4_unicode_ci'), nullable=False,
                  default="https://res.cloudinary.com/dtcxjo4ns/image/upload/v1732252873/tieu-thuyet_u0ymle.png")
    def __str__(self):
        return self.name


class Book(BaseModel):
    __tablename__ = 'book'
    name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    standard_price = Column(DECIMAL(18, 2), nullable=False, default=0)
    unit_price = Column(DECIMAL(18, 2), nullable=False, default=0)
    available_quantity = Column(Integer, nullable=False, default=0)
    is_enable = Column(Boolean, nullable=False, default=True)  # 1:còn bán,0:hết bán
    image = Column(String(255, 'utf8mb4_unicode_ci'), nullable=False,
                   default="https://res.cloudinary.com/dtcxjo4ns/image/upload/v1732252871/temp-16741118072528735594_qnbjoi.jpg")
    discount = Column(DECIMAL, nullable=False,default=0)
    description = Column(Text)

    reviews = relationship('Review', backref='book', lazy=True)  # 1-n

    authors = db.relationship('Author', secondary='author_book', lazy='subquery',
                              backref=db.backref('book', lazy=True))  # n-n
    categories = db.relationship('Category', secondary='book_category', lazy='subquery',
                                 backref=db.backref('book', lazy=True))  # n-n
    vouchers = db.relationship('Voucher', secondary='book_has_voucher', lazy='subquery',
                               backref=db.backref('book', lazy=True))  # n-n

    orders = relationship('OrderDetail', backref='book')  # n-1
    import_tickets = relationship('ImportDetail', backref='book')  # n-1


author_book = db.Table(
    'author_book',
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('book_id', ForeignKey('book.id'), primary_key=True),
    Column('author_id', ForeignKey('author.id'), primary_key=True),

)

book_category = db.Table(
    'book_category',
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('book_id', ForeignKey('book.id'), primary_key=True),
    Column('category_id', ForeignKey('category.id'), primary_key=True),
)


class Configuration(BaseModel):
    __tablename__ = 'configuration'
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text, nullable=False)
    description = Column(Text)


class PaymentMethod(BaseModel):
    __tablename__ = 'payment_method'
    name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False, unique=True)

    orders = relationship('Order', backref='payment_method', lazy=True)


class Voucher(BaseModel):
    __tablename__ = 'voucher'
    name = Column(String(100, 'utf8mb4_unicode_ci'), nullable=False)
    uses = Column(Integer, nullable=False, default=0)  # số lượng voucher đã sử dụng
    max_uses = Column(Integer, nullable=False,
                      default=0)  # Số lượng tối đa voucher có thể sử dụng. Nếu =0 là không xác định
    max_users_uses = Column(Integer, nullable=False,
                            default=0)  # Người dùng có thể sử dụng voucher này bao nhiêu lần? Nếu =0 là không xác định
    type = Column(Boolean, nullable=False, default=1, unique=True)  # Loại voucher: #1: voucher, #2: coupon
    discount_amount = Column(DOUBLE, default=0)  # % giảm giá hoặc số tiền giảm giá cụ thể
    start_date = Column(DateTime, nullable=False)  # Ngày bắt đầu voucher
    end_date = Column(DateTime, nullable=False)  # Ngày kết thúc voucher
    deleted_at = Column(DateTime)  # Ngày xóa


book_has_voucher = db.Table('book_has_voucher', BaseModel.metadata,
                            Column('book_id', Integer, ForeignKey('book.id')),
                            Column('voucher_id', Integer, ForeignKey('voucher.id'))
                            )


class UserHasVoucher(BaseModel):
    __tablename__ = 'user_has_voucher'
    user_id = Column(ForeignKey('user.id'), nullable=False, index=True)
    voucher_id = Column(ForeignKey('voucher.id'), nullable=False, index=True)


class RoleHasPermission(BaseModel):
    __tablename__ = 'role_has_permission'
    role_id = Column(ForeignKey('role.id'), nullable=False, index=True)
    permission_id = Column(ForeignKey('permission.id'), nullable=False, index=True)


class ImportTicket(BaseModel):
    __tablename__ = 'import_ticket'
    import_date = Column(DateTime, nullable=False, default=func.now())
    employee_id = Column(ForeignKey('user.id'), nullable=False, index=True)

    books = relationship('ImportDetail', backref="import_ticket")


class Review(BaseModel):
    __tablename__ = 'review'
    user_id = Column(ForeignKey('user.id'), nullable=False, index=True)
    book_id = Column(ForeignKey('book.id'), nullable=False, index=True)
    comment = Column(Text, nullable=False)  # Nội dung Đánh giá
    rating = Column(Float, nullable=False)  # Số điểm đánh giá: từ 0 -> 5 sao


class Permission(BaseModel):
    __tablename__ = 'permission'
    name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    display_name = Column(String(45, 'utf8mb4_unicode_ci'))


class UserHasPermission(BaseModel):
    __tablename__ = 'user_has_permission'

    user_id = Column(ForeignKey('user.id'), nullable=False, index=True)
    permission_id = Column(ForeignKey('permission.id'), nullable=False, index=True)


class ImportDetail(BaseModel):
    __tablename__ = 'import_detail'
    ticket_id = Column(ForeignKey('import_ticket.id'), nullable=False, index=True)
    book_id = Column(ForeignKey('book.id'), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    standard_price = Column(DECIMAL(18, 4), nullable=False)


class OrderDetail(BaseModel):
    __tablename__ = 'order_detail'

    order_id = Column(ForeignKey('order.id'), nullable=False, index=True)
    book_id = Column(ForeignKey('book.id'), nullable=False, index=True)
    unit_price = Column(DECIMAL(18, 4), nullable=False)
    quantity = Column(Integer, nullable=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # read data from json:
        with open('../app/static/data_import/book_data.json', 'rb') as f:
            data = json.load(f)
            for book in data:
                name = str(book['title']).strip()
                description = str(book['description']).strip()
                image = str(book['image']).strip()
                standard_price = random.randint(20, 200) * 1000
                sell_price = int(standard_price * 1.25)
                discount = random.choice([0, 20])

                categories = []
                for category_name in book['category']:
                    category_name = str(category_name).strip()
                    db_category = Category.query.filter_by(name=category_name).first()
                    if not db_category:
                        db_category = Category(name=category_name)
                        db.session.add(db_category)
                        db.session.flush()  # Đẩy vào DB để lấy ID ngay lập tức
                    if db_category not in categories:
                        categories.append(db_category)
                authors = []
                for author_name in book['author']:
                    author_name = str(author_name).strip()
                    last_name, first_name = author_name.split(' ', 1) if ' ' in author_name else ("",author_name)
                    db_author = Author.query.filter_by(last_name=last_name, first_name = first_name).first()
                    if not db_author:
                        db_author = Author(first_name=first_name, last_name=last_name)
                        db.session.add(db_author)
                        db.session.flush()  # Đẩy vào DB để lấy ID ngay lập tức
                    if db_author not in authors:
                        authors.append(db_author)

                new_book = Book(name= name,
                                description=description,
                                image=image,
                                standard_price=standard_price,
                                unit_price=sell_price,
                                available_quantity=random.randint(100, 300),
                                discount= discount,
                                is_enable=True,
                                )

                # Gán categories và authors cho sách, tránh trùng lặp
                new_book.categories.extend([c for c in categories if c not in new_book.categories])
                new_book.authors.extend([a for a in authors if a not in new_book.authors])

                db.session.add(new_book)
            db.session.commit()
        # END read data from json

        #Cap nhật ảnh cho category
        json_file_path = "path/to/your/json_file.json"

        # Đọc file JSON
        with open('../app/static/data_import/category.json', 'rb') as f:
            data = json.load(f)

        # Cập nhật cơ sở dữ liệu
        for item in data:
            # Tìm thể loại theo tên
            cate = Category.query.filter_by(name=item["name"]).first()
            if cate:
                # Cập nhật đường dẫn ảnh
                cate.image = item["image_url"]
                db.session.add(cate)  # Đánh dấu đối tượng để cập nhật

        # Lưu thay đổi vào cơ sở dữ liệu
        db.session.commit()