import hashlib
import math
from app import app, login, dao, utils, db
from flask import render_template, request, redirect, session, jsonify, url_for, flash, get_flashed_messages
from flask_login import login_user, logout_user, current_user, login_required
from app.dao import delete_from_favourites
from app.utils import cart_stats
from app.vnpay.form import PaymentForm
from app.vnpay.vnpay import Vnpay
from datetime import datetime
import logging
import re
import datetime

@app.route("/")
def index():
    page = request.args.get('page', 1)
    cate_id = request.args.get('category_id')
    kw = request.args.get('kw')
    prods = dao.load_book(latest_books=1)
    banner = dao.load_banner()
    feature_books = dao.load_feature_book()
    cates = dao.get_category()
    total = dao.count_books()
    category_ids = dao.load_category_ids()
    return render_template("index.html",
                           banner=banner,
                           feature_books=feature_books,
                           new_books=prods,
                           category_ids=category_ids,
                           categories=cates,
                           )


@app.route("/register", methods=['get', 'post'])
def register_process():
    err_msg = {'username': '', 'password': '', 'phone': '', 'email': '', 'confirm': ''}
    if 'email_attempts' not in session:
        session['email_attempts'] = 0
    # Kiểm tra xem 'email_attempts' đã tồn tại trong session hay chưa
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        phone = request.form.get('phone')
        email = request.form.get('email')
        gender = True if request.form.get('radioGender') == 'male' else False
        customer = dao.get_user_by_phone(phone)

        # Kiểm tra mật khẩu có khớp không
        if len(password) < 6:
            err_msg['password'] = 'Mật khẩu phải có ít nhất 6 ký tự!'
        if not password == confirm:
            err_msg['confirm'] = 'Mật khẩu không khớp!'

        # Kiểm tra số điện thoại
        if not re.match(r'^\d{10,11}$', phone):
            err_msg['phone'] = 'Số điện thoại phải có 10-11 chữ số!'
        # Kiểm tra email đúng định dạng
        if not email:
            err_msg['email'] = 'Email không được để trống!'
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            session['email_attempts'] += 1
            err_msg['email'] = 'Email không đúng định dạng!'
            if session['email_attempts'] >= 2:
                err_msg['email'] += ' Ví dụ: example@domain.com'

        # Kiểm tra tên đăng nhập đã tồn tại
        if dao.existing_user(username):
            err_msg['username'] = 'Tên đăng nhập đã được sử dụng!'
        # Kiểm tra phone đã tồn tại
        if dao.existing_phone(phone):
            err_msg['phone'] = 'Số điện thoại đã được sử dụng!'

        if customer:
            if customer.username and customer.password:
                # Nếu đã có username và password, số điện thoại đã được sử dụng cho tài khoản online
                err_msg['phone'] = 'Số điện thoại đã được đăng kí tài khoản!'
            else:
                # Nếu chưa có username và password, cập nhật thông tin
                customer.username = username
                customer.email = email
                customer.gender = gender
                customer.password = password  # Hash mật khẩu trước khi lưu
                dao.save_user(customer)
                flash("Đăng kí thành công!", "success")
                return redirect(url_for("login_process"))

        # Nếu không có lỗi, thực hiện đăng ký
        if not any(err_msg.values()):  # Kiểm tra xem có lỗi không
            session.pop('email_attempts', None)  # Reset số lần thử khi thành công
            data = request.form.copy()
            city = data['city']
            district = data['district']
            ward = data['ward']
            street = data['street']

            address_id = dao.add_address(city, district, ward, street)

            del data['confirm']
            del data['radioGender']
            del data['city']
            del data['district']
            del data['ward']
            del data['street']

            avatar = request.files.get('avatar')
            data['gender'] = gender

            dao.add_user(address_id=address_id, avatar=avatar, **data)
            flash("Đăng ký thành công!", "success")
            return redirect(url_for("login_process"))  # Giả sử route cho trang đăng nhập là 'login'

    return render_template('register.html', err_msg=err_msg)


@app.route("/login", methods=['get', 'post'])
def login_process():
    err_msg = None
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        u = dao.auth_user(username=username, password=password)
        if u:
            session['user_id'] = u.id
            login_user(user=u)
            n = request.args.get('next')
            return redirect(n if n else '/')
        else:
            err_msg = 'Tên đăng nhập hoặc mật khẩu không chính xác'

    return render_template('login.html' , err_msg=err_msg)


@app.route("/logout")
def logout_process():
    logout_user()
    return redirect('/')


@app.route('/details', methods=['GET', 'POST'])
def details():
    book_id = request.args.get('book_id')

    # Kiểm tra book_id hợp lệ
    if not book_id or not book_id.isdigit():
        return jsonify({'error': 'ID sách không hợp lệ.'}), 400

    book = dao.load_book(book_id).first()
    if not book:
        return jsonify({'error': 'Sách không tồn tại.'}), 404

    book_activated = book.is_enable
    # book_sold_quantity = book.sold_quantity
    categories = dao.get_category(book_id=book_id)
    current_category = None
    related_books = dao.load_related_book(book)

    # Xử lý breadcrumbs
    current_category_id = request.args.get('category_id')
    if current_category_id:
        current_category = dao.get_category(cate_id=int(current_category_id))
    breadcrumbs = [{'name': 'Trang chủ', 'url': '/'}]
    if current_category:
        breadcrumbs.append({'name': current_category.name, 'url': f"/category?category_id={current_category.id}"})
    else:
        for category in categories:
            breadcrumbs.append({'name': category.name, 'url': f"/category?category_id={category.id}"})
    breadcrumbs.append({'name': book.name, 'url': None})

    # Lấy tên NXB
    publisher = dao.get_publisher_by_book_id(book_id)

    # lấy số lượng đã bán
    sold_quantity = dao.get_sold_quantity(book_id)

    # lấy review
    reviews = dao.load_review(book_id)
    reviews_numbers = len(reviews)
    avg_rating = 0
    if reviews_numbers > 0:
        for r in reviews:
            avg_rating += r.rating
        avg_rating /= reviews_numbers
    else:
        avg_rating = 0

    # Xử lý thêm vào danh sách yêu thích
    if request.method == 'POST':
        if 'user_id' not in session:
            return jsonify({'error': 'Bạn cần đăng nhập để thêm sách vào danh sách yêu thích.'}), 401
        user_id = session['user_id']

        favourite_added = dao.add_to_favourites(user_id=user_id, book_id=book_id)
        if favourite_added:
            return jsonify({'message': 'Đã thêm sách vào danh sách yêu thích thành công.'}), 200
        else:
            return jsonify({'error': 'Sách này đã có trong danh sách yêu thích.'}), 400

    return render_template(
        'details.html',
        book_activated=book_activated,
        related_books=related_books,
        book=book,
        breadcrumbs=breadcrumbs,
        publisher=publisher,
        sold_quantity=sold_quantity,
        reviews=reviews,
        reviews_numbers=reviews_numbers,
        avg_rating=avg_rating

    )


@app.route('/post_comment', methods=['POST', 'GET'])
@login_required
def post_comment():
    data = request.json

    book_id = data.get('book_id')
    comment = data.get('comment')
    rating = data.get('rating')

    if not book_id:
        return jsonify({'error': 'Không có ID sách được gửi.'}), 400
    if not current_user:
        return jsonify({'error': 'Hãy đăng nhập để gửi bình luận. '}), 400
    try:
        book_id = int(data.get('book_id'))
        review = dao.add_review(current_user.id, book_id, comment, rating)

        if review:
            return jsonify({'message': 'Bình luận đã được gửi.'}), 200
        else:
            return jsonify({'error': 'Đã xảy ra lỗi.'}), 404

    except ValueError:
        return jsonify({'error': 'ID sách không hợp lệ.'}), 400


@app.route('/get_comments/<int:book_id>')
def get_comments(book_id):
    reviews = dao.load_review(book_id)

    comments_list = [{
        'user_name': f"{review.first_name} {review.last_name}",
        'comment': review.comment,
        'created_at': review.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        'rating': review.rating,
        'user_id': review.user_id,
        'id': review.id
    } for review in reviews]

    response_data = {
        'comments': comments_list,
        'current_user_id': current_user.id,
        'current_user_role': current_user.role_id
    }
    return jsonify(response_data)


@app.route('/edit_review', methods=['POST'])
def edit_review():
    data = request.json

    review_id = data.get('review_id')
    comment = data.get('comment')
    rating = data.get('rating')

    if not review_id:
        return jsonify({'error': 'Không có ID review được gửi.'}), 400
    try:
        review_id = int(data.get('review_id'))

        review = dao.edit_review(review_id, rating, comment)
        if review:
            return jsonify({'message': 'Bình luận đã được gửi.'}), 200
        else:
            return jsonify({'error': 'Đã xảy ra lỗi.'}), 404

    except ValueError:
        return jsonify({'error': 'ID review không hợp lệ.'}), 400


@app.route('/delete_review', methods=['POST', 'GET'])
def delete_review():
    review_id = request.args.get('review_id')

    try:
        dao.delete_review(review_id)
        return jsonify({'success': True, 'message': 'Bình luận đã được xóa thành công.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@login_required
@app.route('/account')
def account():
    address = dao.load_user_address(current_user.id)
    cart = session.get('cart', {})  # Lấy thông tin giỏ hàng từ session
    cart_quantity = sum(item['quantity'] for item in cart.values())  # Tổng số lượng sản phẩm trong giỏ
    orders_count = dao.get_orders_count(current_user.id)  # Hàm lấy số đơn hàng
    delivering_count = dao.get_delivering_count(current_user.id)  # Hàm lấy số sản phẩm đang giao
    received_count = dao.get_received_count(current_user.id)  # Hàm lấy số sản phẩm đã nhận
    return render_template('account.html',
                           current_user=current_user,
                           address=address,
                           orders_count=orders_count,
                           delivering_count=delivering_count,
                           cart_quantity=cart_quantity,
                           received_count=received_count
                           )


@login_required
@app.route('/favourite', methods=['GET', 'POST'])
def favourite():
    favourite_books = current_user.favourite_books
    return render_template('favourite.html', favourite_books=favourite_books)


@login_required
@app.route('/get_favourites_json', methods=['GET', 'POST'])
def get_favourites_json():
    try:
        favourites = current_user.favourite_books
        favourite_books = [{
            'id': book.id,
            'name': book.name,
            'image': book.image,
            'price': book.unit_price - (book.unit_price * book.discount / 100),
            'unit_price': book.unit_price,
        } for book in favourites]
        return jsonify({'favourite_books': favourite_books}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete_favourite', methods=['POST'])
@login_required
def delete_favourite():
    # Lấy book_id từ request form data
    book_id = request.form.get('book_id')

    # Kiểm tra xem book_id có được gửi lên không
    if not book_id:
        return jsonify({'error': 'Không có ID sách được gửi.'}), 400

    try:
        # Chuyển đổi book_id sang kiểu int nếu cần
        # book_id = int(book_id)
        # Xóa sách khỏi danh sách yêu thích (thêm logic xử lý trong DAO)
        result = dao.delete_from_favourites(current_user.id, book_id)

        if result:
            return jsonify({'message': 'Sách đã được xóa khỏi danh sách yêu thích.'}), 200
        else:
            return jsonify({'error': 'Không tìm thấy sách để xóa hoặc xảy ra lỗi.'}), 404

    except ValueError:
        return jsonify({'error': 'ID sách không hợp lệ.'}), 400


@app.route('/change_password')
@login_required
def change_password():
    return render_template('change_password.html')


@app.route('/api/change_passwd', methods=['POST'])
@login_required
def change_passwd():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')

    if not current_password or not new_password:
        return jsonify({'error': 'Vui lòng nhập đầy đủ thông tin!'}), 400

    if not (hashlib.md5(current_password.encode('utf-8')).hexdigest() == current_user.password):
        return jsonify({'error': 'Mật khẩu hiện tại không chính xác!'}), 403

    try:
        dao.change_password(new_password)
        return jsonify({'message': 'Đổi mật khẩu thành công!'}), 200

    except Exception as e:
        return jsonify({'error': 'Có lỗi xảy ra, vui lòng thử lại!'}), 500


@app.route('/manage_info')
@login_required
def manage_info():
    address = dao.load_user_address(current_user.id)
    return render_template('manage_info.html', current_user=current_user, address=address)


@app.route('/manage_user_info', methods=['POST'])
@login_required
def manage_user_info():
    # Lấy dữ liệu JSON từ yêu cầu
    data = request.get_json()

    # Gọi hàm cập nhật thông tin người dùng từ dao.py
    success = dao.manage_user_info(data)
    # Trả về phản hồi dưới dạng JSON
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/cart', methods=['GET'])
def cart():
    key = app.config['CART_KEY']
    cart = session.get(key)
    has_items = bool(cart)  # Kiểm tra nếu giỏ hàng có sản phẩm (cart không rỗng)
    if current_user.is_authenticated:
        return render_template('cart.html', has_items=has_items)
    else:
        return render_template('cart.html')


@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.json
    id = str(data["id"])
    key = app.config['CART_KEY']
    cart = session[key] if key in session else {}
    quantity = int(data.get("quantity", 1))  # Nếu không có "quantity" trong dữ liệu thì mặc định là 1

    if id in cart:
        cart[id]['quantity'] += quantity
        message = f"Đã thêm thành công {quantity} sản phẩm {cart[id]['name']} vào giỏ hàng!"
    else:
        name = data['name']
        image = data['image']
        unit_price = data['unit_price']

        cart[id] = {
            "id": id,
            "image": image,
            "name": name,
            "unit_price": unit_price,
            "quantity": quantity
        }
        message = f"Đã thêm thành công {quantity} sản phẩm {name} vào giỏ hàng!"
    session[key] = cart

    return jsonify({'message': message,
                    'cart_stats': utils.cart_stats(cart=cart)})


@app.route('/api/cart/<book_id>', methods=['put'])
def update_cart(book_id):
    key = app.config['CART_KEY']
    cart = session.get(key)
    if cart and book_id in cart:
        cart[book_id]['quantity'] = int(request.json['quantity'])

    session[key] = cart

    return jsonify(utils.cart_stats(cart=cart))


@app.route('/api/cart/<book_id>', methods=['delete'])
def delete_cart(book_id):
    key = app.config['CART_KEY']
    cart = session.get(key)

    if cart and book_id in cart:
        message = f"Đã xóa sản phẩm {cart[book_id]['name']} khỏi giỏ hàng thành công!"
        del cart[book_id]

    session[key] = cart
    return jsonify({'message': message,
                    'cart_stats': utils.cart_stats(cart=cart)})


@app.context_processor
def common_attr():
    categories = dao.get_category()
    return {
        'categories': categories,
        'cart': utils.cart_stats(session.get(app.config['CART_KEY']))
    }


@app.route('/category', methods=['GET'])
def category():
    page = request.args.get('page', 1)
    page_size = app.config["PAGE_SIZE"]
    all_price_ranges = ['0-50000', '50000-200000', '200000-infinity']
    ORDER_BY_OPTIONS = [
        {'value': 'totalBuy-DESC', 'label': 'Bán chạy nhất'},
        {'value': 'created_at-DESC', 'label': 'Mới nhất'},
        {'value': 'unit_price-ASC', 'label': 'Giá thấp nhất'}
    ]

    # Lấy id category từ query params
    cate_id = request.args.get('category_id')

    # Lấy thông tin category từ database
    cate = dao.get_category(cate_id)

    # Lấy các tiêu chí lọc từ request
    checked_publishers = request.args.getlist('checkedPublishers')
    price_ranges = request.args.getlist('priceRanges')
    order_param = request.args.get('order', 'unit_price-ASC')
    order_by, order_dir = order_param.split('-')  # Tách tên cột và chiều sắp xếp

    books, total_products = dao.filter_books(category_id=cate_id,
                                             checked_publishers=checked_publishers,
                                             price_ranges=price_ranges,
                                             order_by=order_by,
                                             order_dir=order_dir,
                                             page=int(page)
                                             )
    publishers = dao.get_publishers_by_category(cate_id)

    # Render template với dữ liệu
    return render_template(
        'category.html',
        category=cate,
        total_products=total_products,
        pages=math.ceil(total_products / page_size),
        products=books,
        publishers=publishers,
        checked_publishers=checked_publishers,
        price_ranges=price_ranges,
        order=order_param,
        all_price_ranges=all_price_ranges,
        ORDER_BY_OPTIONS=ORDER_BY_OPTIONS,
        current_page=int(page),
    )


@app.route('/categories', methods=['GET'])
def all_categories():
    page = request.args.get('page', 1)
    page_size = app.config["PAGE_SIZE"]
    all_price_ranges = ['0-50000', '50000-200000', '200000-infinity']
    ORDER_BY_OPTIONS = [
        {'value': 'totalBuy-DESC', 'label': 'Bán chạy nhất'},
        {'value': 'created_at-DESC', 'label': 'Mới nhất'},
        {'value': 'unit_price-ASC', 'label': 'Giá thấp nhất'}
    ]
    order_param = request.args.get('order', 'unit_price-ASC')
    order_by, order_dir = order_param.split('-')

    # Lấy tất cả thể loại category từ database
    cate = dao.get_category()
    category_id = request.args.get('category_id')
    # current_category = Category.query.get(category_id)

    # Lấy các tiêu chí lọc từ request
    checked_publishers = request.args.getlist('checkedPublishers')
    price_ranges = request.args.getlist('priceRanges')
    order_param = request.args.get('order', 'totalBuy-DESC')
    order_by, order_dir = order_param.split('-')  # Tách tên cột và chiều sắp xếp
    books, total_products = dao.filter_books(checked_publishers=checked_publishers,
                                             price_ranges=price_ranges,
                                             order_by=order_by,
                                             order_dir=order_dir,
                                             page=int(page)
                                             )
    publishers = dao.get_all_publishers()

    # Render template
    return render_template(
        'all_categories.html',
        category=cate,
        total_products=total_products,
        pages=math.ceil(total_products / page_size),
        products=books,
        publishers=publishers,
        checked_publishers=checked_publishers,
        price_ranges=price_ranges,
        order=order_param,
        all_price_ranges=all_price_ranges,
        ORDER_BY_OPTIONS=ORDER_BY_OPTIONS,
        current_page=int(page),
    )


@app.route("/login-admin", methods=['post'])
def login_admin_process():
    username = request.form.get('username')
    password = request.form.get('password')
    allowed_roles = ["Admin", "Customer", "Sales", "Storekeeper"]  # Cac role co san
    user = dao.auth_user(username=username, password=password, role=allowed_roles)
    if user:
        login_user(user)
    return redirect('/admin')


@app.route("/search", methods=['GET'])
def live_search():
    query = request.args.get('q', '').strip().lower()
    if query:
        try:
            results = dao.search(query)
            books = [{"name": book.name, "price": book.standard_price, "id": book.id, "image": book.image} for book in
                     results]
            return jsonify({"success": True, "data": books})

        except Exception as ex:
            return jsonify({"success": False, "message": str(ex), "data": []}), 500
    return jsonify({"success": False, "message": "Query is empty", "data": []})


@app.route('/search_result')
def search_result():
    query = request.args.get('q', '').strip().lower()
    print(query)
    books = []
    if query:
        books = dao.search(query)
        print(books)
    return render_template('search_result.html', books=books)


@app.route('/api/pay', methods=['POST'])
def api_pay():
    try:
        data = request.json
        order_id = data.get('order_id', '123456')
        amount = data.get('amount', 100000)
        order_desc = data.get('order_desc', 'Thanh toán')
        bank_code = data.get('bank_code', '')

        vnp = Vnpay()
        vnp.requestData = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': app.config["VNPAY_TMN_CODE"],  # Kiểm tra mã TMN code
            'vnp_Amount': amount * 100,  # Nhân 100 để đưa về VNĐ
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': order_id,  # Mã đơn hàng duy nhất
            'vnp_OrderInfo': order_desc,
            'vnp_OrderType': 'billpayment',
            'vnp_Locale': 'vn',
            'vnp_BankCode': bank_code,
            'vnp_ReturnUrl': app.config["VNPAY_RETURN_URL"]  # URL trả về sau thanh toán
        }

        # Kiểm tra dữ liệu trước khi tạo URL
        print("Request Data:", vnp.requestData)

        payment_url = vnp.get_payment_url(
            'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html',
            app.config["VNPAY_HASH_SECRET_KEY"]
        )

        # Log URL thanh toán
        print("Payment URL:", payment_url)

        return jsonify({'status': 200, 'payment_url': payment_url})
    except Exception as e:
        return jsonify({'status': 500, 'message': str(e)})


@app.route("/statistic", methods=['GET'])
def statistic():
    month = int(request.args.get("month"))
    type = request.args.get("type")
    data = None
    if type == 'book':
        data = utils.statistic_book_by_month(month)
    if type == 'category':
        data = utils.statistic_category_by_month(month)
    if type == 'overall':
        data = utils.statistic_revenue()
    return data


@app.route('/api/save_import_ticket', methods=['POST'])
def save_import_ticket():
    data = request.json
    employee_id = current_user.id
    import_date = data.get('import_date')
    details = data.get('details')
    if not employee_id or not import_date or not details:
        return jsonify({'error': 'Dữ liệu không hợp lệ!'})
    # Gọi dao để lưu phiếu nhập

    ticket_id = dao.save_import_ticket(
        employee_id=employee_id,
        import_date=import_date,
        details=details
    )
    return jsonify({'message': 'Phiếu nhập đã được lưu thành công!', 'ticket_id': ticket_id})


@app.route("/payment_return", methods=["GET"])
def payment_return():
    if request.args:
        vnp = Vnpay()
        vnp.responseData = request.args.to_dict()
        order_id = request.args.get('vnp_TxnRef')
        amount = int(request.args.get('vnp_Amount')) / 100
        order_desc = request.args.get('vnp_OrderInfo')
        vnp_BankTranNo = request.args.get("vnp_BankTranNo")
        vnp_TransactionNo = request.args.get('vnp_TransactionNo')
        vnp_ResponseCode = request.args.get('vnp_ResponseCode')
        print(vnp_ResponseCode)
        vnp_PayDate = request.args.get('vnp_PayDate')
        vnp_BankCode = request.args.get('vnp_BankCode')
        vnp_CardType = request.args.get('vnp_CardType')
        vnp_SecureHash = request.args.get('vnp_SecureHash')
        if vnp.validate_response(app.config["VNPAY_HASH_SECRET_KEY"]):
            if vnp_ResponseCode == "00":
                dao.order_paid_by_vnpay(order_id=int(order_id[0:2:1]), bank_transaction_number=vnp_BankTranNo,
                                        vnpay_transaction_number=vnp_TransactionNo, bank_code=vnp_BankCode,
                                        card_type=vnp_CardType, secure_hash=vnp_SecureHash, received_money=amount,
                                        paid_date=vnp_PayDate)
                return render_template("vnpay/payment_return.html", title="Kết quả giao dịch",
                                       result="Thành công", order_id=order_id,
                                       amount=amount,
                                       order_desc=order_desc,
                                       vnp_TransactionNo=vnp_TransactionNo,
                                       vnp_ResponseCode=vnp_ResponseCode)
            else:
                return render_template("vnpay/payment_return.html", title="Kết quả giao dịch",
                                       result="Lỗi", order_id=order_id,
                                       amount=amount,
                                       order_desc=order_desc,
                                       vnp_TransactionNo=vnp_TransactionNo,
                                       vnp_ResponseCode=vnp_ResponseCode)
        else:
            return render_template("vnpay/payment_return.html",
                                   title="Kết quả giao dịch", result="Lỗi", order_id=order_id, amount=amount,
                                   order_desc=order_desc, vnp_TransactionNo=vnp_TransactionNo,
                                   vnp_ResponseCode=vnp_ResponseCode, msg="Sai checksum")
    else:
        return render_template("vnpay/payment_return.html", title="Kết quả thanh toán", result="")


@app.route("/my_order")
@login_required
def myOrder():
    page = request.args.get('page', 1)
    page_size = 4
    current_page = int(page)
    orders = dao.get_orders_by_customer_id(current_user.id, page=int(page))
    orders_with_total = []
    for order in orders:
        total_payment = dao.calculate_order_total(order.id)  # Tính tổng tiền cho đơn hàng
        orders_with_total.append({
            "order": order,
            "total_payment": total_payment
        })
    quantity_order = dao.count_orders_by_customer_id(current_user.id)
    return render_template('my_order.html', title='Order Books', orders_with_total=orders_with_total,
                           datetime=datetime.datetime,
                           current_page=int(page),
                           pages=math.ceil(quantity_order / page_size),
                           quantity_order=quantity_order
                           )


@app.route("/order_details")
@login_required
def order_details():
    order_id = request.args.get("order_id")
    order = dao.get_order_by_id(order_id=order_id)
    order_details = dao.get_order_details(order_id)
    payment_method = dao.get_payment_method_by_order_id(order_id)
    user_info = dao.get_user_info_in_order(current_user.id, order_id)

    total_payment = dao.calculate_order_total(order_id)  # Tính tổng tiền cho đơn hàng
    return render_template("order_details.html", order_details=order_details, user_order_info=user_info,
                           order_id=order_id, total_payment=total_payment, order=order,
                           datetime=datetime.datetime, payment_method=payment_method)


# @app.route("/api/order/cash/pay", methods = ["POST"])
# def intable_pay_order():
#     try:
#         order_id = int(request.json.get("order_id"))
#         received_money = int(request.json.get("received_money"))
#         print(order_id, received_money)
#         if utils.order_paid_incash(received_money, order_id) == 0:
#             utils.order_delivered(order_id)
#             return jsonify({"code": 200})
#         else:
#             return jsonify({"code": 402})
#     except Exception as e:
#         print(e)
#         return jsonify({"code": 400})


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    key = app.config['CART_KEY']
    configuration = dao.get_configuration()
    payment_methods = dao.get_payment_method_all()
    # Xử lý logic cho GET và POST
    if request.method == 'GET':
        # Chuẩn bị dữ liệu cho form
        customer = current_user
        user_address = dao.get_user_address(customer.id)  # Lấy địa chỉ của customer

        form_data = {
            "customer_id": customer.id,
            "full_name": f"{customer.first_name} {customer.last_name}",
            "phone_number": customer.phone,
            "email": customer.email,
            "city": user_address["city"],
            "district": user_address["district"],
            "ward": user_address["ward"],
            "details": user_address["details"]
        }
        return render_template('checkout.html', form_data=form_data, payment_methods=payment_methods)

    elif request.method == 'POST':
        # Lấy dữ liệu từ request.form
        customer_id = request.form.get("customer_id")
        full_name = request.form.get("full_name")
        phone_number = request.form.get("phone_number")
        email = request.form.get("email")
        city = request.form.get("city")
        district = request.form.get("district")
        ward = request.form.get("ward")
        details = request.form.get("details")
        payment_type = request.form.get("payment_type")

        # Xử lý logic tạo đơn hàng
        # staff tạo đơn hàng cho khách hàng mua trực tiếp
        if int(customer_id) != current_user.id:
            customer = dao.get_user_by_id(int(customer_id))
            staff = current_user
        else:
            # khách hàng mua online
            customer = current_user
            staff = dao.get_user_by_username("saler")
        order = dao.create_order(customer.id, staff.id, session['cart'], payment_type)

        session[key] = {}  # Xóa cart sau khi tạo đơn hàng
        session.modified = True

        # nhân viên bán hàng tạo đơn hàng cho khách mua trực tiếp
        if (current_user.id != customer.id):
            if (order.payment_method.name.__eq__("CASH")):
                flash("New order has been created", "success")
                return redirect(url_for("users.staff"))
        else:
            address = dao.get_user_address(current_user.id)
            if not address or address["city"] != city or address["district"] != district or address["ward"] != ward or \
                    address["details"] != details:
                # Tạo địa chỉ mới nếu có thay đổi
                new_address = dao.add_address(city=city, district=district, ward=ward, street=details)

                # Cập nhật `address_id` cho user
                current_user.address_id = new_address
                order.delivered_at = new_address
                db.session.commit()
            else:
                order.delivered_at = current_user.address_id
                db.session.commit()
                # Cập nhật số điện thoại nếu cần
            if current_user.phone != phone_number:
                current_user.phone = phone_number
                db.session.commit()
        if payment_type == "2":
            return redirect(url_for("process_vnpay", order_id=order.id, user_id=customer.id))
        else:
            return redirect(url_for("myOrder"))
    return render_template('checkout.html')


@app.route("/vnpay", methods=["GET", "POST"])
@login_required
def process_vnpay():
    form = PaymentForm()
    if request.method == 'POST':
        # Process input data and build url payment
        if form.validate_on_submit():
            order_type = form.order_type.data
            order_id = form.order_id.data
            amount = int(form.amount.data)
            order_desc = form.order_desc.data
            bank_code = form.bank_code.data
            language = form.language.data
            ipaddr = request.remote_addr
            # Build URL Payment
            vnp = Vnpay()
            vnp.requestData['vnp_Version'] = '2.1.0'
            vnp.requestData['vnp_Command'] = 'pay'
            vnp.requestData['vnp_TmnCode'] = app.config["VNPAY_TMN_CODE"]
            vnp.requestData['vnp_Amount'] = amount * 100
            vnp.requestData['vnp_CurrCode'] = 'VND'
            vnp.requestData['vnp_TxnRef'] = str(order_id) + "_" + datetime.datetime.now().__str__()
            vnp.requestData['vnp_OrderInfo'] = order_desc
            vnp.requestData['vnp_OrderType'] = order_type
            # Check language, default: vn
            if language and language != '':
                vnp.requestData['vnp_Locale'] = language
            else:
                vnp.requestData['vnp_Locale'] = 'vn'
                # Check bank_code, if bank_code is empty, customer will be selected bank on VNPAY
            if bank_code and bank_code != "":
                vnp.requestData['vnp_BankCode'] = bank_code

            vnp.requestData['vnp_CreateDate'] = datetime.datetime.now().strftime('%Y%m%d%H%M%S')  # 20150410063022
            vnp.requestData['vnp_IpAddr'] = ipaddr
            vnp.requestData['vnp_ReturnUrl'] = app.config["VNPAY_RETURN_URL"]
            vnpay_payment_url = vnp.get_payment_url(app.config["VNPAY_PAYMENT_URL"],
                                                    app.config["VNPAY_HASH_SECRET_KEY"])
            return redirect(vnpay_payment_url)
        else:
            print("Form input not validate")
    else:
        order_id = int(request.args.get("order_id"))
        user_id = int(request.args.get("user_id"))
        order = dao.get_order_by_id(order_id)
        user = dao.get_user_by_id(user_id)
        if not order:
            flash("Order not found", "danger")
            return redirect(url_for("checkout"))
        if not user:
            flash("User not found", "danger")
            return redirect(url_for("checkout"))
        form.order_id.data = order.id
        form.amount.data = dao.calculate_order_total(order.id)
        form.order_desc.data = "%s thanh toán online cho cửa hàng bookstore3h" % (
            user.last_name+ user.first_name)
        return render_template("vnpay/payment.html", title="Kiểm tra thông tin", form=form)


def user_to_dict(user):
    address = user.Address  # Truy cập thông tin địa chỉ từ quan hệ Address
    return {
        "phone": user.phone,
        "full_name": f"{user.first_name} {user.last_name}",
        "email": user.email,
        "city": address.city if address else None,
        "district": address.district if address else None,
        "ward": address.ward if address else None,
        "details": address.details if address else None,
    }


@app.route('/get-customer', methods=['GET'])
def get_customer():
    phone_number = request.args.get('phone_number')
    customers = dao.load_User()
    customer = next((c for c in customers if c.phone == phone_number), None)
    if customer:
        return jsonify({"status": "success", "data": user_to_dict(customer)})
    else:
        return jsonify({"status": "not_found", "message": "Không tìm thấy thông tin khách hàng."})

@app.route('/api/process_order', methods=['POST'])
def process_order():
    try:
        data = request.get_json()
        phone = data.get('phone')
        # Kiểm tra thông tin khách hàng theo số điện thoại
        user = dao.get_user_by_phone(phone)

        if not user:
            # Tạo khách hàng mới nếu chưa tồn tại
            user = dao.new_user_in_order(
                phone=phone,
                full_name=data.get('full_name'),
            )

        # Tạo đơn hàng
        order = dao.add_order_in_order(
            customer_id=user.id,
            received_money=data['total_payment'],
            payment_method_id=data['payment_method_id'],
            order_details=data['order_details']
        )

        return jsonify({
            'success': True,
            'message': 'Đơn hàng đã được tạo thành công',
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400


@app.route('/revenue-stats', methods=['GET'])
def revenue_stats():
    # Lấy tháng và năm từ query parameters
    month = request.args.get('month', default=None, type=int)
    year = request.args.get('year', default=datetime.now().year, type=int)

    # Nếu người dùng chỉ truyền `year` thì dùng hàm `revenue_stats_by_time` cho cả năm
    if month is None:
        stats = dao.revenue_stats_by_time(year=year)
    else:
        stats = dao.revenue_stats_by_time(time='month', year=year)

        # Lọc thêm theo tháng
        stats = [stat for stat in stats if stat[0] == month]

    return render_template('admin\chart.html', stats=stats)
@app.route("/cancel_order", methods=["POST"])
@login_required
def cancel_order():
    data = request.get_json()
    order_id = data.get("order_id")
    # Cập nhật trạng thái đơn hàng trong cơ sở dữ liệu
    success = dao.cancel_order(order_id, current_user.id)

    if success:
        print("Hủy đơn hàng thành công")
        return jsonify({"message": "Hủy đơn hàng thành công"}), 200
    else:
        print("Không thể hủy đơn hàng")
        return jsonify({"error": "Hủy đơn hàng thất bại"}), 400


if __name__ == '__main__':
    with app.app_context():
        from app import admin

        app.run(debug=True)