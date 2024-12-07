import math
from app import app, login, dao
from flask import render_template, request, redirect,session, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app.dao import delete_from_favourites


@app.route("/")
def index():
    page = request.args.get('page', 1)
    cate_id = request.args.get('category_id')
    kw = request.args.get('kw')
    prods = dao.load_book(latest_books=1)
    banner = dao.load_banner()
    feature_books = dao.load_book()
    cates = dao.get_category()
    total = dao.count_products()
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

            dao.add_user(address_id=address_id,avatar=avatar, **data)

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
            print(u.id)
            login_user(user=u)
            print('thanh cong')
            return redirect('/')
        else:
            print("ko thanh cong")
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
        # book_sold_quantity=book_sold_quantity
    )

@login_required
@app.route('/account')
def account():
    address = dao.load_user_address(current_user.id)
    return render_template('account.html',
                           current_user=current_user,
                           address=address
                           )

@app.route('/favourite', methods=['GET','POST'])
def favourite():
    favourite_books = current_user.favourite_books
    # print('this', favourite_books)
    return render_template('favourite.html', favourite_books=favourite_books)



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

        # Xóa sách khỏi danh sách yêu thích (thêm logic xử lý trong DAO)
        result = dao.delete_from_favourites(current_user.id, book_id)

        if result:
            return jsonify({'message': 'Sách đã được xóa khỏi danh sách yêu thích.'}), 200
        else:
            return jsonify({'error': 'Không tìm thấy sách để xóa hoặc xảy ra lỗi.'}), 404

    except ValueError:
        return jsonify({'error': 'ID sách không hợp lệ.'}), 400

@app.route('/change_password')
def change_password():
    return render_template('change_password.html')

@app.route('/manage_info')
def manage_info():
    return render_template('manage_info.html')


@app.route("/login-admin", methods=['post'])
def login_admin_process():
    pass
    # username = request.form.get('username')
    # password = request.form.get('password')
    #
    # u = dao.auth_user(username=username, password=password, role=UserRole.ADMIN)
    # if u:
    #     login_user(u)
    #
    # return redirect('/admin')



@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/cart', methods=['GET'])
def cart():
    return render_template('cart.html')

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
        cate= dao.get_category(cate_id)

        # Lấy các tiêu chí lọc từ request
        checked_publishers = request.args.getlist('checkedPublishers')
        price_ranges = request.args.getlist('priceRanges')
        order_param = request.args.get('order', 'unit_price-ASC')
        order_by, order_dir = order_param.split('-')  # Tách tên cột và chiều sắp xếp

        # Đếm tổng số sản phẩm với các tiêu chí lọc
        total_products = dao.count_products(category_id=cate_id,
                                         checked_publishers=checked_publishers,
                                        price_ranges=price_ranges)

        books=dao.get_products_by_filters(category_id=cate_id,
                                          checked_publishers=checked_publishers,
                                          price_ranges=price_ranges,
                                        order_by=order_by,
                                          order_dir=order_dir,
                                          page=int(page)
                                          )

        publishers = dao.get_publishers_by_category(cate_id)
        print(books)

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

if __name__ == '__main__':
    with app.app_context():
      app.run(debug=True)