import hashlib
import math

from app import app, login, dao, utils
from flask import render_template, request, redirect, session, jsonify, url_for
from flask_login import login_user, logout_user, current_user, login_required
from app.dao import delete_from_favourites
from app.vnpay.form import PaymentForm
from app.vnpay.vnpay import Vnpay


@app.route("/")
def index():
    page = request.args.get('page', 1)
    cate_id = request.args.get('category_id')
    kw = request.args.get('kw')
    prods = dao.load_book(latest_books=1)
    banner = dao.load_banner()
    feature_books = dao.load_feature_book()
    print(feature_books)
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
    err_msg = ''

    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        gender = True if request.form.get('radioGender') == 'male' else False

        if not password.__eq__(confirm):
            err_msg = 'Mật khẩu không khớp!'
        if dao.existing_user(username):
            err_msg = 'Tên đăng nhập đã được sử dụng!'
        else:
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

            return redirect('/login')

    return render_template('register.html', err_msg=err_msg)


@app.route("/login", methods=['get', 'post'])
def login_process():
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        u = dao.auth_user(username=username, password=password)
        if u:
            session['user_id'] = u.id
            login_user(user=u)
            n=request.args.get('next')
            return redirect(n if n else '/')
    return render_template('login.html')


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
        avg_rating=0

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
        review = dao.add_review(current_user.id, book_id, comment, rating )

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
        'id':review.id
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
    return render_template('account.html',
                           current_user=current_user,
                           address=address
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

@app.route('/api/change_passwd', methods = ['POST'])
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
    return jsonify({'message':message,
                    'cart_stats':utils.cart_stats(cart=cart)})

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


@app.route('/api/pay')
@login_required
def pay():
    key = app.config['CART_KEY']
    cart = session.get(key)
    try:
        dao.save_order(cart)
    except:
        return jsonify({'status': 500})
    else:
        del session[key]
    return jsonify({'status': 200})

@app.context_processor
def common_attr():
    categories=dao.get_category()
    return {
        'categories':categories,
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

    books = dao.filter_books(category_id=cate_id,
                            checked_publishers=checked_publishers,
                            price_ranges=price_ranges,
                            order_by=order_by,
                            order_dir=order_dir,
                            page=int(page)
                             )
    print(books)
    total_products=dao.count_books(books)
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


@app.route('/order')
def order():
    return render_template('order.html')



@app.route("/login-admin", methods=['post'])
def login_admin_process():
    username = request.form.get('username')
    password = request.form.get('password')
    allowed_roles = ["Admin", "Customer", "Sales", "Storekeeper"] #Cac role co san
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
            books = [{"name": book.name, "price": book.standard_price, "id": book.id, "image": book.image} for book in results]
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

# @app.route('/orders/process_vnpay', methods=['POST'])
# def process_vnpay():
#     form = PaymentForm(request.form)
#     if form.validate_on_submit():
#         vnp = Vnpay()
#         vnp.requestData = {
#             'vnp_Version': '2.1.0',
#             'vnp_Command': 'pay',
#             'vnp_TmnCode': app.config["VNPAY_TMN_CODE"],
#             'vnp_Amount': form.amount.data * 100,  # Số tiền phải *100
#             'vnp_CurrCode': 'VND',
#             'vnp_TxnRef': form.order_id.data,
#             'vnp_OrderInfo': form.order_desc.data,
#             'vnp_OrderType': form.order_type.data,
#             'vnp_Locale': form.language.data,
#             'vnp_BankCode': form.bank_code.data,
#             'vnp_ReturnUrl': app.config["VNPAY_PAYMENT_URL"]
#         }
#
#         payment_url = vnp.get_payment_url(app.config["VNPAY_PAYMENT_URL"], app.config["VNPAY_HASH_SECRET_KEY"])
#         return redirect(payment_url)
#     else:
#         return "Invalid Form Data", 400

@app.route('/payment_return', methods=['GET'])
def payment_return():
    vnp = Vnpay()
    vnp.responseData = request.args.to_dict()  # Lấy dữ liệu từ URL callback của VNPay

    # Kiểm tra tính hợp lệ của dữ liệu trả về
    if vnp.validate_response(app.config["VNPAY_HASH_SECRET_KEY"]):
        response_code = vnp.responseData.get('vnp_ResponseCode')
        if response_code == '00':  # Giao dịch thành công
            dao.order_paid_by_vnpay(
                order_id=vnp.responseData.get('vnp_TxnRef'),
                bank_transaction_number=vnp.responseData.get('vnp_TransactionNo'),
                vnpay_transaction_number=vnp.responseData.get('vnp_TransactionNo'),
                bank_code=vnp.responseData.get('vnp_BankCode'),
                card_type=vnp.responseData.get('vnp_CardType'),
                secure_hash=vnp.responseData.get('vnp_SecureHash'),
                received_money=int(vnp.responseData.get('vnp_Amount')) // 100,
                paid_date=vnp.responseData.get('vnp_PayDate')
            )
            return "Payment Success"
        else:
            return "Payment Failed"
    else:
        return "Invalid Response"

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
            'vnp_TxnRef': order_id,      # Mã đơn hàng duy nhất
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

@app.route('/save_import_ticket', methods=['POST'])
def save_import_ticket():
    data = request.json
    role_id=current_user.id
    # Lấy thông tin từ request
    employee_id = data.get('employee_id')
    import_date = data.get('import_date')
    details = data.get('details')

    if not employee_id or not import_date or not details:
        return jsonify({'error': 'Dữ liệu không hợp lệ!'}), 400
    # Gọi dao để lưu phiếu nhập
    ticket_id = dao.save_import_ticket(
        employee_id=employee_id,
        import_date=import_date,
        details=details
    )
    return jsonify({'message': 'Phiếu nhập đã được lưu thành công!', 'ticket_id': ticket_id})

if __name__ == '__main__':
    with app.app_context():
        from app import admin
        app.run(debug=True)