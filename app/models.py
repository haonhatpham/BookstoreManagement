from enum import Enum as StatusEnum
from app import db, app
from flask_login import UserMixin
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Boolean, Text, DECIMAL, DOUBLE, Enum, DATE
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
import hashlib
import json, random, os
import uuid
from flask_security import Security, SQLAlchemyUserDatastore, permissions_accepted
import string
from datetime import datetime, timedelta


class OrderEnum(StatusEnum):
    GIAOHANGTHANHCONG = 1
    DANGGIAOHANG = 2
    HUYDONHANG = 3


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Publisher(BaseModel):
    __tablename__ = 'publishers'

    name = db.Column(db.String(255), nullable=False)
    books = db.relationship('Book', backref='publisher', lazy=True)

    def __str__(self):
        return self.name


class Role(BaseModel):
    __tablename__ = 'role'
    name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False, unique=True)
    description = Column(String(45, 'utf8mb4_unicode_ci'))

    permissions = relationship('Permission', secondary='role_has_permission', lazy='subquery',
                               backref=backref('roles', lazy=True))
    users = relationship('User', backref='role', lazy=True)


favourite_books = db.Table(
    'user_has_favourite_books',
    db.Column('id', Integer, primary_key=True, autoincrement=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'))
)


class Address(BaseModel):
    __tablename__ = 'address'
    city = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    district = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    ward = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    details = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)

    users = relationship("User", backref='Address', lazy=True)


class User(BaseModel, UserMixin):
    __tablename__ = 'user'
    first_name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    last_name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    email = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    phone = Column(String(11, 'utf8mb4_unicode_ci'))
    birth = Column(DATE, nullable=True)
    gender = Column(Boolean, default=True)  # 1:nam 0:Nữ
    avatar_file = Column(String(255, 'utf8mb4_unicode_ci'), nullable=True)
    active = Column(Boolean, default=True)  # 1: còn hđ 0:hết hđ

    role_id = Column(ForeignKey(Role.id), nullable=False, index=True)
    address_id = Column(ForeignKey(Address.id), index=True,nullable=True)

    customer_orders = relationship("Order", backref="customer", lazy=True, foreign_keys='Order.customer_id')  # 1-n
    employee_orders = relationship("Order", backref="employee", lazy=True, foreign_keys='Order.employee_id')  # 1-n
    reviews = relationship('Review', backref='user', lazy=True)  # 1-n
    import_tickets = relationship('ImportTicket', backref='user', lazy=True)  # 1-n
    vouchers = db.relationship('Voucher', secondary='user_has_voucher', lazy='subquery',
                               backref=db.backref('users', lazy=True))  # n-n
    permission = db.relationship('Permission', secondary='user_has_permission', lazy='subquery',
                                 backref=backref('users', lazy=True))  # n-n
    favourite_books = db.relationship('Book', secondary=favourite_books, back_populates='users')
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))


class Order(BaseModel):
    __tablename__ = 'order'
    customer_id = Column(ForeignKey(User.id), index=True, nullable=False)
    employee_id = Column(ForeignKey(User.id), index=True, nullable=False)
    initiated_date = Column(DateTime, nullable=False)
    cancel_date = Column(DateTime, nullable=False)
    total_payment = Column(Integer, nullable=False)
    received_money = Column(Integer, nullable=True)
    paid_date = Column(DateTime, nullable=True)
    delivered_date = Column(DateTime, nullable=True, default=None)
    status = Column(Enum(OrderEnum), nullable=False)
    payment_method_id = Column(ForeignKey('payment_method.id'), index=True, nullable=False, default=1)

    books = relationship('OrderDetail', backref='order')
    banking_information = relationship('BankingInformation', backref='order', lazy=True, uselist=False)  # 1-1


class BankingInformation(BaseModel):
    __tablename__ = 'banking_information'
    order_id = Column(ForeignKey(Order.id), unique=True, nullable=False)  # 1-1
    bank_transaction_number = Column(String(255), nullable=False)
    vnpay_transaction_number = Column(String(20), nullable=False)
    card_type = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    bank_code = Column(String(20, 'utf8mb4_unicode_ci'), nullable=False)
    secure_hash = Column(String(256), nullable=False)


class Author(BaseModel):
    __tablename__ = 'author'
    first_name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    last_name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)


class Category(BaseModel):
    __tablename__ = 'category'
    name = Column(String(200, 'utf8mb4_unicode_ci'), nullable=False, unique=True)
    image = Column(String(200, 'utf8mb4_unicode_ci'), nullable=False,
                   default="https://res.cloudinary.com/dtcxjo4ns/image/upload/v1732252873/tieu-thuyet_u0ymle.png")

    def __str__(self):
        return self.name


class Book(BaseModel):
    __tablename__ = 'book'
    name = Column(String(45, 'utf8mb4_unicode_ci'), nullable=False)
    standard_price = Column(DECIMAL(18, 2), nullable=False, default=0)
    unit_price = Column(DECIMAL(18, 2), nullable=False, default=0)
    available_quantity = Column(Integer, nullable=False, default=0)
    # sold_quantity = Column(Integer,default=0)
    is_enable = Column(Boolean, nullable=False, default=True)  # 1:còn bán,0:hết bán
    image = Column(String(255, 'utf8mb4_unicode_ci'), nullable=False,
                   default="https://res.cloudinary.com/dtcxjo4ns/image/upload/v1732252871/temp-16741118072528735594_qnbjoi.jpg")
    discount = Column(DECIMAL, nullable=False, default=0)
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
    users = db.relationship('User', secondary=favourite_books, back_populates='favourite_books')
    year_publishing = db.Column(db.Integer, nullable=False)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.id'), nullable=False)


author_book = db.Table(
    'author_book',
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('book_id', ForeignKey('book.id')),
    Column('author_id', ForeignKey('author.id')),

)

book_category = db.Table(
    'book_category',
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('book_id', ForeignKey('book.id')),
    Column('category_id', ForeignKey('category.id')),
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
    comment = Column(Text, nullable=False)
    rating = Column(Float, nullable=False)


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
        # đọc data từ file json
        with open('../app/static/data_import/book_data.json', 'rb') as f:
            data = json.load(f)
            for book in data:
                name = str(book['title']).strip()
                description = str(book['description']).strip()
                image = str(book['image']).strip()
                standard_price = random.randint(20, 200) * 1000
                sell_price = int(standard_price * 1.25)
                discount = random.choice([0, 20])
                year_publishing = book['year_publishing']

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
                    last_name, first_name = author_name.split(' ', 1) if ' ' in author_name else ("", author_name)
                    db_author = Author.query.filter_by(last_name=last_name, first_name=first_name).first()
                    if not db_author:
                        db_author = Author(first_name=first_name, last_name=last_name)
                        db.session.add(db_author)
                        db.session.flush()  # Đẩy vào DB để lấy ID ngay lập tức
                    if db_author not in authors:
                        authors.append(db_author)
                # NXB
                publisher_name = str(book['publisher']).strip()
                db_publisher = Publisher.query.filter_by(name=publisher_name).first()
                if not db_publisher:
                    db_publisher = Publisher(name=publisher_name)
                    db.session.add(db_publisher)
                    db.session.flush()  # Đẩy vào DB để lấy ID ngay lập tức
                new_book = Book(name=name,
                                description=description,
                                image=image,
                                standard_price=standard_price,
                                unit_price=sell_price,
                                available_quantity=random.randint(100, 300),
                                discount=discount,
                                is_enable=True,
                                publisher_id=db_publisher.id,
                                year_publishing=year_publishing,
                                # sold_quantity=sold_quantity
                                )

                # Gán categories và authors cho sách, tránh trùng lặp
                new_book.categories.extend([c for c in categories if c not in new_book.categories])
                new_book.authors.extend([a for a in authors if a not in new_book.authors])

                db.session.add(new_book)
            db.session.commit()
        # END read data from json

        # Cap nhật ảnh cho category
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
        admin_role = Role(name="Admin", description="Administrator with full access")
        customer_role = Role(name="Customer", description="Role for registered customers")
        sales_role = Role(name="Sales", description="Role for sales staff")
        storekeeper = Role(name="Storekeeper", description="Role for storekeeper staff")
        db.session.add_all([admin_role, customer_role, sales_role, storekeeper])
        db.session.commit()
        #
        test_admin_role = Role.query.filter_by(name="Admin").first()
        # Lưu vai trò vào database
        admin_user = User(
            first_name="Nhật Hào",
            last_name="Phạm",
            username="admin",
            password=str(hashlib.md5("123456".encode('utf-8')).hexdigest()),
            email="admin@example.com",
            phone="1234567890",
            birth="2004-10-08",  # Không cần ngày sinh
            gender=True,  # Nam
            avatar_file="https://res.cloudinary.com/dtcxjo4ns/image/upload/v1732976606/dd7862a2-d925-464f-8729-69c6f71f4960_bborg7.jpg",
            active=True,
            role_id=test_admin_role.id  # Liên kết với vai trò Admin
        )
        db.session.add(admin_user)
        db.session.commit()
        test_staff_role = Role.query.filter_by(name="Sales").first()
        test_staff = User(
            first_name='Saler',
            last_name='2024',
            username='saler',
            password=str(hashlib.md5("123456".encode('utf-8')).hexdigest()),
            email='saler@example.com',
            phone="1234567891",
            birth="2004-01-01",
            gender=False,
            avatar_file="https://res.cloudinary.com/dtcxjo4ns/image/upload/v1733467650/photo_sspnsa.jpg",
            active=True,
            role_id=test_staff_role.id,
        )
        db.session.add(test_staff)
        db.session.commit()
        test_warehouse_role = Role.query.filter_by(name="Storekeeper").first()
        test_warehouse_staff = User(
            first_name='storekeeper',
            last_name='2024',
            username='thukho',
            password=str(hashlib.md5("123456".encode('utf-8')).hexdigest()),
            email='storekeeper@example.com',
            phone="0987654321",
            birth="2000-12-08",
            gender=True,
            avatar_file="https://res.cloudinary.com/dtcxjo4ns/image/upload/v1733422179/vien-ngoc-trai-ki-dieu_bia_abb1f5dda267482e861d051f77bd41e1_master_v4sroz.jpg",
            active=True,
            role_id=test_warehouse_role.id  # Lấy ID của vai trò "Warehouse"
        )
        db.session.add(test_warehouse_staff)
        db.session.commit()

        # payment method
        in_cash = PaymentMethod(name='CASH')
        internet_banking = PaymentMethod(name='BANKING')
        db.session.add_all([in_cash, internet_banking])
        db.session.commit()

        first_names = [
            'Harry', 'Amelia', 'Oliver', 'Jack', 'Isabella', 'Charlie', 'Sophie', 'Mia',
            'Jacob', 'Thomas', 'Emily', 'Lily', 'Ava', 'Isla', 'Alfie', 'Olivia', 'Jessica',
            'Riley', 'William', 'James', 'Geoffrey', 'Lisa', 'Benjamin', 'Stacey', 'Lucy'
        ]

        last_names = [
            'Brown', 'Smith', 'Patel', 'Jones', 'Williams', 'Johnson', 'Taylor', 'Thomas',
            'Roberts', 'Khan', 'Lewis', 'Jackson', 'Clarke', 'James', 'Phillips', 'Wilson',
            'Ali', 'Mason', 'Mitchell', 'Rose', 'Davis', 'Davies', 'Rodriguez', 'Cox', 'Alexander'
        ]

        def random_birthday(start_year=1980, end_year=2005):
            start_date = datetime(start_year, 1, 1)
            end_date = datetime(end_year, 12, 31)
            delta = end_date - start_date
            random_days = random.randint(0, delta.days)
            return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')




        for i in range(len(first_names)):
            tmp_email = first_names[i].lower() + "." + last_names[i].lower() + "@example.com"
            # tmp_pass = ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(10))
            phone = "0"
            random_birth = random_birthday()
            temp_role = Role.query.filter_by(name="Customer").first()
            for k in range(0, 9):
                phone += str(random.randint(6, 9))

            temp_user = User(
                first_name=first_names[i],
                last_name=last_names[i],
                username=f'user{i}',
                password=str(hashlib.md5("123456".encode('utf-8')).hexdigest()),
                email=tmp_email,
                phone=phone,
                birth=random_birth,
                gender=random.choice([True, False]),
                avatar_file="https://res.cloudinary.com/dtcxjo4ns/image/upload/v1733412995/Remove-bg.ai_1733412613451_jyuilr.png",
                active=True,
                role_id=temp_role.id  # Lấy ID của vai trò "Customer"
            )
            db.session.add(temp_user)
            db.session.commit()

            # QUI ĐỊNH
            rules = [
                {"key": "time_to_cancel_order", "value": "48",
                 "description": "Time in hours before an unpaid online order is canceled."},
                {"key": "min_import_quantity", "value": "150", "description": "Minimum quantity for book import."},
                {"key": "max_stock_for_import", "value": "300", "description": "Maximum stock allowed to import books."}
            ]

            # Insert rules into the configuration table
            for rule in rules:
                existing_rule = Configuration.query.filter_by(key=rule["key"]).first()
                if existing_rule:
                    print(f"Rule with key '{rule['key']}' already exists. Skipping.")
                    continue

                new_rule = Configuration(
                    key=rule["key"],
                    value=rule["value"],
                    description=rule["description"],
                    created_at=datetime.now()
                )
                db.session.add(new_rule)

            db.session.commit()
        permissons= [
            {"name": "view_stats", "display_name": " Thống kê"},
            {"name": "manage_books", "display_name": "Quản lý sách"},
            {"name": "create_order", "display_name": "Lập hóa đơn"},
            {"name": "import_book", "display_name": "Nhập sách"},
            {"name": "change_rules", "display_name": "Thay đổi quy định"},
            {"name":"order_book","display_name":"Đặt sách"}
        ]
        for p in permissons :
            existing_permission = Permission.query.filter_by(name=p['name']).first()
            if not existing_permission:
                permission = Permission(name=p['name'], display_name=p['display_name'])
                db.session.add(permission)
        db.session.commit()
        admin_role = Role.query.filter_by(name="Admin").first()
        customer_role = Role.query.filter_by(name="Customer").first()
        sales_role = Role.query.filter_by(name="Sales").first()
        storekeeper = Role.query.filter_by(name="Storekeeper").first()

        all_permissions = Permission.query.all()
        admin_role.permissions = [
            permission for permission in all_permissions
            if permission.name in ["view_stats", "manage_books", "create_order", "import_book", "change_rules"]
        ]

        sales_role.permissions = [
            permission for permission in all_permissions
            if permission.name == "create_order"
        ]


        storekeeper.permissions = [
            permission for permission in all_permissions
            if permission.name == "import_book"
        ]


        customer_role.permissions = [
            permission for permission in all_permissions
            if permission.name == "view_stats"
        ]



        db.session.commit()






