from app.models import Category, Book, User, book_category,Role,Publisher
from app import app, db
import hashlib
import cloudinary.uploader
from sqlalchemy import desc, engine, or_
from sqlalchemy.orm import session, sessionmaker

Session = sessionmaker(bind=engine)
session = Session()


#load banner_home
def load_banner():
    books_banner = Book.query.limit(4).all()
    return books_banner

#load sách tieu bieu ở home
def load_feature_book():
    # feature_book = Book.query.offset(4).limit(6).all()
    # return feature_book
    pass #sách tiêu biểu sẽ xử lí theo số lượng có mặt của sách đó trong đơn hàng nên sẽ xử lí sau
#lay sach theo id
def load_book(book_id=None):
    if book_id:
        return Book.query.filter(Book.id == book_id)
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
def get_category(cate_id=None,book_id=None):
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

#
def load_new_products(kw=None, cate_id=None, page=1):
    query = Book.query.order_by(desc(Book.id))
    if kw:
        query = query.filter(Book.name.contains(kw))
    if cate_id:
        query = query.join(book_category, book_category.c.book_id == Book.id) \
            .filter(book_category.c.category_id == cate_id)
    page_size = app.config["PAGE_SIZE"]
    start = (page - 1) * page_size
    query = query.slice(start, start + page_size)

    return query.all()

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

#Thêm user ở Client
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

#chứng thực tài khoản khi đăng nhập
def auth_user(username, password):
    password = hashlib.md5(password.encode('utf-8')).hexdigest()

    return User.query.filter(User.username.__eq__(username.strip()),
                             User.password.__eq__(password)).first()

#Lấy user theo id
def get_user_by_id(id):
    return User.query.get(id)

#Lấy id các nhà xuất bản sách theo tên
def get_publisher_ids_by_names(names):
    publishers = Publisher.query.filter(Publisher.name.in_(names)).all()
    return [publisher.id for publisher in publishers]

#Lọc danh sách các sách theo: nxb, giá, và sắp xếp theo ORDERBY,...
def get_products_by_filters(category_id, checked_publishers,price_ranges, order_by, order_dir,page=1):
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
            print(min_price,max_price)
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

#Lấy nhà xuất bản theo id của thể loại
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
