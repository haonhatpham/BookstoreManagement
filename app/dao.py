import logging

from flask import jsonify
from flask_login import current_user
from sqlalchemy.testing.suite.test_reflection import users
from sqlalchemy import func
from app.models import Book, Category, User, book_category, Role, Publisher, favourite_books, Configuration, \
    PaymentMethod, Order, OrderEnum, OrderDetail, BankingInformation, Address, Review
from datetime import datetime, timedelta
from app import app, db
import hashlib
import cloudinary.uploader
from sqlalchemy import desc, engine, or_, func
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
    query = (
        Book.query
        .join(OrderDetail, OrderDetail.book_id == Book.id)  # JOIN giữa bảng Book và OrderDetail
        .with_entities(
            Book.id,
            Book.name,
            Book.unit_price,
            Book.discount,
            Book.image,
            func.count(OrderDetail.id)  # Tính số lượng xuất hiện của sách
        )
        .group_by(Book.id, Book.name, Book.unit_price, Book.discount)  # Nhóm theo các trường
        .order_by(func.count(OrderDetail.id).desc())  # Sắp xếp theo số lượng đã bán (giảm dần)
        .limit(10)  # Lấy top 10 sách tiêu biểu
    )

    # Trả về kết quả của truy vấn
    return query.all()

# lay sach theo id
def load_book(book_id=None, latest_books=None):
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

def existing_user(username):
    return User.query.filter_by(username=username).first()


def add_address(city, district, ward, street):
    address = Address(
        city=city.strip(),
        district=district.strip(),
        ward=ward.strip(),
        details=street.strip()
    )
    db.session.add(address)
    db.session.commit()
    # trả về id để khi gọi hàm ngoài index.py, id sẽ được thêm vào User.address_id
    return address.id


def load_user_address(user_id):
    return (
        Address.query
        .join(User, Address.id == User.address_id)
        .filter(User.id == user_id)
        .first()
    )


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
        u.avatar_file = res.get("secure_url")

    db.session.add(u)
    db.session.commit()


# # chứng thực tài khoản khi đăng nhập
# def auth_user(username, password):
#     password = hashlib.md5(password.encode('utf-8')).hexdigest()
#
#     return User.query.filter(User.username.__eq__(username.strip()),
#                              User.password.__eq__(password)).first()

def auth_user(username, password, role=None):
    password = hashlib.md5(password.encode('utf-8')).hexdigest()

    u = User.query.filter(
        User.username == username.strip(),
        User.password == password
    )
    if role:  # Nếu có yêu cầu kiểm tra vai trò
        u = u.join(Role).filter(Role.name == role)

    return u.first()

def change_password(new_password):
    user = (User.query
        .filter(User.id == current_user.id)
        .first()
    )
    password = hashlib.md5(new_password.encode('utf-8')).hexdigest()
    user.password = password

    db.session.commit()
    return user

def manage_user_info(data):
    try:
        user = User.query.filter_by(username=data['username']).first()
        user_address = Address.query.filter(Address.id == user.address_id).first()

        if user:
            # Cập nhật thông tin người dùng
            user.name = data['name']
            name_parts = data['name'].strip().split(" ", 1)
            if len(name_parts) > 1:
                user.first_name = name_parts[1]
                user.last_name = name_parts[0]
            else:
                # Nếu không có dấu cách, mặc định đặt last_name là name và first_name rỗng
                user.first_name = ''
                user.last_name = name_parts[0]

            user.email = data['email']
            user.phone = data['phone_number']
            user.gender = data['gender']
            user_address.city = data['city']
            user_address.district = data['district']
            user_address.ward = data['ward']
            user_address.details = data['street']

            db.session.commit()
            return True
        else:
            return False

    except Exception as e:
        db.session.rollback()  # Rollback trong trường hợp có lỗi
        print(f"Error updating user info: {e}")
        return False

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

def count_books(book_objects=None):
    if book_objects:
        # Trường hợp có danh sách các đối tượng sách
        return len(book_objects)
    else:
        # Trường hợp không có danh sách, trả về tổng số sách trong cơ sở dữ liệu
        return Book.query.count()

# Lọc danh sách các sách theo: nxb, giá, và sắp xếp theo ORDERBY,...
def filter_books(category_id, checked_publishers, price_ranges, order_by, order_dir, page=1):
    books = Book.query
    from sqlalchemy.sql import text

    # Subquery tính tổng số lượng bán được (totalBuy)
    total_buy_subquery = db.session.query(OrderDetail
                                          .book_id.label('book_id'),
                                          func.sum(OrderDetail.quantity).label('totalBuy')
                                          ).group_by(OrderDetail.book_id).subquery()

    # Join subquery với bảng Book
    books = books.outerjoin(total_buy_subquery, Book.id == total_buy_subquery.c.book_id)


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
            if max_price == "infinity":
                # Lọc các sản phẩm có giá >= min_price
                price_conditions.append(Book.unit_price >= float(min_price))
            else:
                # Lọc các sản phẩm có giá nằm trong khoảng min_price và max_price
                price_conditions.append(Book.unit_price.between(float(min_price), float(max_price)))

        books = books.filter(or_(*price_conditions))

    # Sắp xếp theo order_by và order_dir
    if order_by == 'totalBuy':  # Trường hợp sắp xếp theo totalBuy
        books = books.order_by(
            total_buy_subquery.c.totalBuy.desc() if order_dir == 'DESC' else total_buy_subquery.c.totalBuy)
    elif hasattr(Book, order_by):
        books = books.order_by(
            getattr(Book, order_by).desc() if order_dir == 'DESC' else getattr(Book, order_by),
            Book.id.desc() if order_dir == 'DESC' else Book.id
        )
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


def get_sold_quantity(book_id):
    book_sold = (OrderDetail.query
                 .filter(OrderDetail.book_id == book_id)
                 .all()
                 )
    sold_quantity = 0
    for i in range(len(book_sold)):
        sold_quantity += book_sold[i].quantity
    return sold_quantity

    # book_available = (Book.query
    #                   .filter(Book.id==book_id))


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


def save_order_sampledb(order):
    db.session.add(order)
    db.session.commit()


def save_order(cart):
    if cart:
        r = Order(customer=current_user)
        db.session.add(r)

        for c in cart.values():
            d = OrderDetail(quantity=c['quantity'],
                            unit_price=c['unit_price'],
                            order_id=r,book_id=c['id'])
            db.session.add(d)
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
    save_order_sampledb(order)
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

    save_order_sampledb(order)
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
    save_order_sampledb(order)
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
            save_order_sampledb(order)
            return 0


def add_review(user_id, book_id, comment, rating):
    review = Review(
        user_id=user_id,
        book_id=book_id,
        comment=comment,
        rating=rating
    )
    db.session.add(review)
    db.session.commit()
    return review


def load_review(book_id):
    return (User.query
            .join(Review, User.id == Review.user_id)
            .with_entities(User.first_name, User.last_name, User.role_id, Review.created_at, Review.comment, Review.rating, Review.user_id, Review.id)
            .filter(Review.book_id == book_id)
            .order_by(Review.created_at.desc())
            .all()

            )

def edit_review(review_id, rating, comment):
    review = Review.query.filter(Review.id == review_id).first()
    review.rating = rating
    review.comment = comment
    db.session.commit()
    return review

def delete_review(review_id):
    (Review.query.filter(Review.id == review_id).delete())
    db.session.commit()



def count_product_by_cate():
    return db.session.query(Category.id, Category.name, func.count(Book.id)) \
        .join(book_category, book_category.c.category_id == Category.id, isouter=True) \
        .join(Book, book_category.c.book_id == Book.id) \
        .group_by(Category.id).all()



def stats_revenue(kw=None):
    query = db.session.query(Book.id, Book.name, func.sum(OrderDetail.quantity * OrderDetail.unit_price)) \
        .join(OrderDetail, OrderDetail.book_id.__eq__(Book.id))
    if kw:
        query = query.filter(Book.name.contains(kw))

    return query.group_by(Book.id).order_by(Book.id).all()

def search(kw):
    try:
        if not kw or len(kw) < 3:
            return []
        query = (Book.query
                 .filter(
                    (Book.name.ilike(f'%{kw}%'))
                 )
                 .all()
                 )
        return query
    except Exception as ex:
        logging.error(f"Error during search: {str(ex)}")
        return []

def statistic_revenue():
    return db.session.query(
        func.extract("month", Order.paid_date).label("month"),  # Lấy tháng từ paid_date trong Order
        func.sum(OrderDetail.quantity * OrderDetail.unit_price).label("revenue")  # Tính doanh thu
    ) \
    .join(Order, Order.id == OrderDetail.order_id).group_by(func.extract("month", Order.paid_date)).order_by(func.extract("month", Order.paid_date)).all()
def stat_category_by_month(month):
    return db.session.query(
        Category.name,
        func.count(OrderDetail.book_id),
        func.sum(OrderDetail.quantity * OrderDetail.unit_price).label("revenue")
    ) \
    .join(book_category, book_category.c.category_id == Category.id) \
    .join(Book, book_category.c.book_id == Book.id) \
    .join(OrderDetail, Book.id == OrderDetail.book_id) \
    .join(Order, OrderDetail.order_id == Order.id) \
    .group_by(Category.name) \
    .filter(func.extract("month", Order.paid_date) == month) \
    .order_by(desc("revenue")) \
    .all()

def stat_book_by_month(month):
    category_list = func.group_concat(Category.name).label("categories")
    return db.session.query(
        Book.name,
        category_list,
        func.sum(OrderDetail.quantity).label("quantity")
    ) \
    .join(OrderDetail, Book.id == OrderDetail.book_id) \
    .join(Order, OrderDetail.order_id == Order.id) \
    .join(book_category, book_category.c.book_id == Book.id) \
    .join(Category, book_category.c.category_id == Category.id) \
    .group_by(Book.name) \
    .filter(func.extract("month", Order.paid_date) == month) \
    .order_by(desc("quantity")) \
    .all()


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

        # Address
        cities = [
            'Hanoi', 'Ho Chi Minh City', 'Da Nang', 'Hai Phong', 'Can Tho',
            'Hue', 'Nha Trang', 'Vung Tau', 'Da Lat', 'Quy Nhon',
            'Long Xuyen', 'Rach Gia', 'Thai Nguyen', 'Thanh Hoa', 'Vinh',
            'Dong Hoi', 'Ha Long', 'Cam Ranh', 'Phan Rang', 'Phan Thiet',
            'Pleiku', 'Buon Ma Thuot', 'Kon Tum', 'My Tho', 'Soc Trang'
        ]

        districts = [
            'Ba Dinh', 'Thanh Xuan', 'Cau Giay', 'Binh Thanh', 'Tan Binh',
            'Hai Chau', 'Son Tra', 'Lien Chieu', 'Le Chan', 'Ngo Quyen',
            'Ninh Kieu', 'Cai Rang', 'Thuan An', 'Di An', 'Tan Uyen',
            'Xuan Phu', 'Phu Hoi', 'Hai Ba Trung', 'Dong Da', 'Hoan Kiem',
            'Thach That', 'Soc Son', 'Hoai Duc', 'Thanh Tri', 'Ha Dong'
        ]

        wards = [
            'Ngoc Ha', 'Khuong Dinh', 'Dich Vong', 'Ward 12', 'Ward 6',
            'Thuan Phuoc', 'An Hai Bac', 'Man Thai', 'Tran Nguyen Han', 'Ngo Quyen',
            'Hung Loi', 'An Cu', 'Binh Hoa', 'Tan Dong Hiep', 'Phu My',
            'Thuy Xuan', 'Phu Cat', 'Hai Tan', 'Trung Hoa', 'Quang An',
            'Tay Ho', 'Mai Dich', 'Yen So', 'Van Quan', 'Mo Lao'
        ]

        details = [
            '123 Nguyen Trai Street', '456 Tran Hung Dao Street', '789 Le Loi Avenue',
            '12 Phan Dinh Phung Street', '34 Vo Thi Sau Street',
            '56 Bach Dang Street', '78 Hai Ba Trung Street', '90 Ngo Quyen Street',
            '23 Hoang Hoa Tham Street', '45 Ly Thai To Street',
            '67 Pasteur Street', '89 Dien Bien Phu Street', '101 Vo Van Tan Street',
            '222 Ly Chinh Thang Street', '333 Cach Mang Thang Tam Street',
            '444 Truong Dinh Street', '555 Le Hong Phong Street', '666 Pham Van Dong Street',
            '777 Nguyen Van Linh Street', '888 Ton Duc Thang Street',
            '999 Bui Thi Xuan Street', '1010 Huynh Tan Phat Street', '1111 Truong Sa Street',
            '1212 Hoang Dieu Street', '1313 Tran Phu Street'
        ]

        address_ids = []
        for a in range(len(cities)):
            address = add_address(cities[a], districts[a], wards[a], details[a])
            address_ids.append(address)
        users = User.query.all()
        for u in users:
            u.address_id = random.choice(address_ids)
        db.session.commit()

        # Comment
        books = Book.query.all()
        comments = [
            'Great work on this project! The results are impressive and clearly show the effort put into development. The attention to detail in the implementation stands out, and it has significantly improved the user experience. Keep up the excellent work!',
            'Consider optimizing the code for better performance. While the functionality is solid, some areas of the code could benefit from refactoring to reduce redundancy and improve efficiency. This would also make the system easier to maintain in the long run.',
            'The documentation is clear and helpful, making it easy for others to understand how the system works. Including additional examples and potential use cases would further enhance its value, especially for new developers joining the team.',
            'There seems to be a bug when handling edge cases, such as unexpected input formats or extreme values. It would be great to add more test cases to ensure robustness and prevent these issues from occurring in production environments.',
            'The design is intuitive and user-friendly, making it easy for users to navigate the interface. However, it might be worth exploring additional features, such as customization options or advanced settings, to cater to a broader range of user needs.'
        ]

        user_ids = [user.id for user in users]
        book_ids = [book.id for book in books]

        for r in range(len(book_ids)):
            review = add_review(
                user_id=random.choice(user_ids),
                book_id=r + 1,
                comment=random.choice(comments),
                rating=random.randint(1, 5)
            )
