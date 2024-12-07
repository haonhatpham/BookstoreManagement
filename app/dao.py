from flask import jsonify
from flask_login import current_user
from app.models import Book,Category,User,book_category,Role,Publisher,favourite_books,Configuration,PaymentMethod,Order,OrderEnum,OrderDetail,BankingInformation,Address
from datetime import datetime,timedelta
from app import app, db
import hashlib
import cloudinary.uploader
from sqlalchemy import desc, engine, or_
from sqlalchemy.orm import session, sessionmaker
import random

Session = sessionmaker(bind=engine)
session = Session()


# load banner_home
def load_banner():
    books_banner = Book.query.limit(4).all()
    return books_banner


# load sách tieu bieu ở home
def load_feature_book():
    # feature_book = Book.query.offset(4).limit(6).all()
    # return feature_book
    pass  # sách tiêu biểu sẽ xử lí theo số lượng có mặt của sách đó trong đơn hàng nên sẽ xử lí sau


# lay sach theo id
def load_book(book_id=None,latest_books=None):
    if book_id:
        return Book.query.filter(Book.id == book_id)
    if latest_books:
        return Book.query.order_by(desc(Book.id))
    return Book.query.all()


def load_related_book(book):
    category_ids = [category.id for category in book.categories]
    return (
        Book.query
        .join(book_category)
        .filter(book_category.c.category_id.in_(category_ids))
        .filter(Book.id != book.id)  # Loại trừ chính cuốn sách hiện tại
        .all()
    )


def load_category_ids():
    category_ids = db.session.query(Category.id).all()
    return [id[0] for id in category_ids]


# Lấy đối tượng category nếu có id_cate truyền vào
# hoặc lấy các categories của 1 book nếu có book truyền vào
# hoặc trả về tất cả đối tượng category
def get_category(cate_id=None, book_id=None):
    if book_id:
        # Lấy các category của book thông qua bảng trung gian book_category
        categories = (Category.query
                      .join(book_category)
                      .filter(book_category.c.book_id == book_id).all())  # Trả về danh sách các category của book
        return categories
    if cate_id:
        # Trả về một category cụ thể
        return Category.query.filter_by(id=cate_id).first()
    else:
        # Trả về toàn bộ category
        return Category.query.all()



def count_products(category_id=None, checked_publishers=None, price_ranges=None):
    # Khởi tạo query
    query = Book.query

    # Nếu có category_id, join với bảng phụ để lọc sách thuộc danh mục này
    if category_id:
        query = query.join(book_category, book_category.c.book_id == Book.id) \
            .filter(book_category.c.category_id == category_id)
    # Lọc theo nhà xuất bản
    if checked_publishers:
        publisher_ids = get_publisher_ids_by_names(checked_publishers)
        query = query.filter(Book.publisher_id.in_(publisher_ids))

    # Lọc theo khoảng giá
    if price_ranges:
        for price_range in price_ranges:
            min_price, max_price = price_range.split('-')
            if max_price == "infinity":
                query = query.filter(Book.unit_price >= min_price)
            else:
                query = query.filter(Book.unit_price.between(min_price, max_price))

    return query.count()

# Thêm user ở Client
def add_user(name, username, password, email, phone, birth, gender, avatar, address_id):
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
        role_id=user_role.id,
        address_id=address_id
    )

    if avatar:
        res = cloudinary.uploader.upload(avatar)
        print(res)
        u.avatar_file = res.get("secure_url")

    db.session.add(u)
    db.session.commit()

# chứng thực tài khoản khi đăng nhập
def auth_user(username, password):
    password = hashlib.md5(password.encode('utf-8')).hexdigest()

    return User.query.filter(User.username.__eq__(username.strip()),
                             User.password.__eq__(password)).first()


# Lấy user theo id
def get_user_by_id(id):
    return User.query.get(id)

# Lấy id các nhà xuất bản sách theo tên
def get_publisher_ids_by_names(names):
    publishers = Publisher.query.filter(Publisher.name.in_(names)).all()
    return [publisher.id for publisher in publishers]

def get_publisher_by_book_id(book_id):
    publisher = (
        db.session.query(Publisher)
        .join(Book, Publisher.id == Book.publisher_id)
        .filter(book_id == Book.id)
        .distinct()
        .first()
    )
    return publisher

def load_user_address(user_id):
    return (
        Address.query
        .join(User, Address.id == User.address_id)
        .filter(User.id == user_id)
        .first()
    )

# Lọc danh sách các sách theo: nxb, giá, và sắp xếp theo ORDERBY,...
def get_products_by_filters(category_id, checked_publishers, price_ranges, order_by, order_dir, page=1):
    books = Book.query
    from sqlalchemy.sql import text

    if category_id:
        books = books.join(book_category, book_category.c.book_id == Book.id) \
            .filter(book_category.c.category_id == category_id)

    if checked_publishers:
        publisher_ids = get_publisher_ids_by_names(checked_publishers)
        books = books.filter(Book.publisher_id.in_(publisher_ids))

    if price_ranges:
        price_conditions = []
        for price_range in price_ranges:
            min_price, max_price = price_range.split('-')
            print(min_price, max_price)
            if max_price == "infinity":
                # Lọc các sản phẩm có giá >= min_price
                price_conditions.append(Book.unit_price >= float(min_price))
            else:
                # Lọc các sản phẩm có giá nằm trong khoảng min_price và max_price
                price_conditions.append(Book.unit_price.between(float(min_price), float(max_price)))

        books = books.filter(or_(*price_conditions))
        print(books)
    # Sắp xếp theo order_by và order_dir
    if hasattr(Book, order_by):
        books = books.order_by(getattr(Book, order_by).desc() if order_dir == 'DESC' else getattr(Book, order_by))
    else:
        raise ValueError(f"Invalid order_by column: {order_by}")

    page_size = app.config["PAGE_SIZE"]
    start = (page - 1) * page_size
    books = books.slice(start, start + page_size)
    return books.all()


# Lấy nhà xuất bản theo id của thể loại
def get_publishers_by_category(category_id):
    publishers = (
        db.session.query(Publisher)
        .join(Book, Publisher.id == Book.publisher_id)  # Liên kết Publisher với Book
        .join(book_category, book_category.c.book_id == Book.id)  # Liên kết Book với category_book
        .filter(book_category.c.category_id == category_id)  # Lọc theo category_id
        .distinct()  # Loại bỏ trùng lặp
        .all()
    )
    return publishers


def add_to_favourites(user_id, book_id):
    existing_favourite = db.session.query(favourite_books).filter_by(user_id=user_id, book_id=book_id).first()
    if existing_favourite:
        return False

    db.session.execute(
        favourite_books.insert().values(user_id=user_id, book_id=book_id)
    )
    db.session.commit()
    return True


def delete_from_favourites(user_id, book_id):
    if user_id and book_id:
        db.session.query(favourite_books).filter_by(user_id=user_id, book_id=book_id).delete()
        db.session.commit()
        return True
    return False


def get_configuration():
    return Configuration.query.first()


def get_payment_method_by_id(id):
    return PaymentMethod.query.get(id)


def save_book(book):
    db.session.add(book)
    db.session.commit()


def save_order(order):
    db.session.add(order)
    db.session.commit()


def save_order_details(order_detail):
    db.session.add(order_detail)
    db.session.commit()


def get_order_by_id(order_id):
    return Order.query.get(order_id)


def get_orders_by_customer_id(customer_id):
    return Order.query.filter_by(customer_id=customer_id).order_by(Order.id.asc()).all()


def save_banking_information(order_id, bank_transaction_number, vnpay_transaction_number, bank_code, card_type,
                             secure_hash):
    infor = BankingInformation(order_id=order_id, bank_transaction_number=bank_transaction_number,
                               vnpay_transaction_number=vnpay_transaction_number, bank_code=bank_code,
                               card_type=card_type, secure_hash=secure_hash)
    db.session.add(infor)
    db.session.commit()
    return infor

def order_delivered(order_id, delivered_date=datetime.now()):
    order = get_order_by_id(order_id)
    if order is None:
        return -1
    order.delivered_date = delivered_date
    save_order(order)
    return 0

def create_order(customer_id, staff_id, books, payment_method_id, initial_date=datetime.now()):
    configuration = get_configuration()
    customer = get_user_by_id(customer_id)
    staff = get_user_by_id(staff_id)
    payment_method = get_payment_method_by_id(payment_method_id)
    # create order details
    order_details = []
    total_payment = 0
    for ordered_book in books:
        book = load_book(book_id=ordered_book['id']).first()
        if book is not None:
            detail = OrderDetail(unit_price=book.unit_price, quantity=ordered_book['quantity'], book=book)
            total_payment += book.unit_price * ordered_book['quantity']
            order_details.append(detail)
            book.available_quantity -= ordered_book['quantity']
            save_book(book)
    # create order
    time_to_cancel_order = db.session.query(Configuration).filter_by(key="time_to_cancel_order").first()
    time_to_cancel_order_hours = 0
    if time_to_cancel_order:
        time_to_cancel_order_hours = int(time_to_cancel_order.value)
    order = Order(cancel_date=initial_date + timedelta(hours=time_to_cancel_order_hours),
                  payment_method=payment_method,
                  customer_id=customer.id,
                  employee_id=staff.id,
                  total_payment=total_payment,
                  initiated_date=initial_date,
                  status=random.choice([OrderEnum.GIAOHANGTHANHCONG, OrderEnum.DANGGIAOHANG, OrderEnum.HUYDONHANG])
                  )

    save_order(order)
    for od in order_details:
        od.order = order
        save_order_details(od)
    return order


def order_paid_incash(received_money, order_id, paid_date=datetime.now()):
    order = get_order_by_id(order_id)
    if order is None or order.paid_date:
        return -1
    if received_money < order.total_payment:
        return -2
    order.received_money = received_money
    order.paid_date = paid_date
    save_order(order)
    return 0


def order_paid_by_vnpay(order_id, bank_transaction_number, vnpay_transaction_number, bank_code, card_type,
                        secure_hash, received_money, paid_date):
    order = get_order_by_id(order_id)
    if not order or order.paid_date:
        return -1
    else:
        infor = save_banking_information(order_id=order_id, bank_transaction_number=bank_transaction_number,
                                         vnpay_transaction_number=vnpay_transaction_number, bank_code=bank_code,
                                         card_type=card_type, secure_hash=secure_hash)
        if infor:
            order.received_money = received_money
            order.paid_date = paid_date
            save_order(order)
            return 0


if __name__ == "__main__":
    with app.app_context():
        # Order
        import datetime

        in_cash = PaymentMethod(name='CASH')
        internet_banking = PaymentMethod(name='BANKING')
        staff_id = 2
        customer_list = User.query.filter(User.id > 3)
        book_list = Book.query.all()
        start_date = datetime.datetime(2024, 1, 1)
        days_increment = 0
        for customer in customer_list:
            random_number = random.randint(4, 7)
            order_details = []
            for i in range(0, random_number):
                b = random.choice(book_list)
                q = random.randint(1, 5)
                f = True
                for o in order_details:
                    if o['id'] == b.id:
                        o['quantity'] += q
                        f = False
                if f:
                    detail = {}
                    detail['id'] = b.id
                    detail['quantity'] = q
                    order_details.append(detail)
            initial_date = start_date + datetime.timedelta(days=days_increment)
            if days_increment > 30 * 12:
                days_increment = 0
            days_increment += 20
            order = create_order(customer.id, staff_id, order_details, in_cash.id, initial_date)
            rand_num = random.randint(1, 10)
            order_paid_incash(order.total_payment, order.id,
                              order.initiated_date + datetime.timedelta(hours=rand_num))
            order_delivered(order.id, order.initiated_date + datetime.timedelta(hours=rand_num + 1))