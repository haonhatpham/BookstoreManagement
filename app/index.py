import math
from app import app, login, dao
from flask import render_template, request, redirect,session, jsonify
from flask_login import login_user, logout_user
from flask_login import current_user



@app.route("/")
def index():
    page = request.args.get('page', 1)
    cate_id = request.args.get('category_id')
    kw = request.args.get('kw')
    prods = dao.load_new_products(cate_id=cate_id, kw=kw, page=int(page))

    banner = dao.load_banner()
    feature_books = dao.load_book()
    cates = dao.get_category()
    page_size = app.config["PAGE_SIZE"]
    total = dao.count_products()
    category_ids = dao.load_category_ids()
    return render_template("index.html",
                           banner=banner,
                           feature_books=feature_books,
                           new_books=prods,
                           category_ids=category_ids,
                           categories=cates,
                           pages=math.ceil(total / page_size))

@app.route("/register", methods=['get', 'post'])
def register_process():
    err_msg = ''

    if request.method.__eq__('POST'):
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        gender = True if request.form.get('radioGender') == 'male' else False

        if not password.__eq__(confirm):
            err_msg = 'Mật khẩu không khớp!'
        else:
            data = request.form.copy()
            del data['confirm']
            del data['radioGender']
            avatar = request.files.get('avatar')
            data['gender'] = gender

            dao.add_user(avatar=avatar, **data)

            return redirect('/login')

    return render_template('register.html', err_msg=err_msg)


@app.route("/login", methods=['get', 'post'])
def login_process():
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        u = dao.auth_user(username=username, password=password)
        if u:
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
@app.route('/details')

def details():
    book_id = request.args.get('book_id')
    book = dao.load_book(book_id).first()
    categories = dao.get_category(book_id=book_id)
    current_category=None

    # Kiểm tra xem có đang truy cập từ một danh mục không
    current_category_id = request.args.get('category_id')  # Lấy danh mục hiện tại từ query
    if current_category_id:
        current_category = dao.get_category(cate_id=int(current_category_id))  # Lấy thông tin danh mục hiện tại
    breadcrumbs = [{'name': 'Trang chủ', 'url': '/'}]
    if current_category:
        breadcrumbs.append({'name': current_category.name, 'url': f"/category?category_id={current_category.id}"})
    else:
        for category in categories:
            breadcrumbs.append({'name': category.name, 'url': f"/category?category_id={category.id}"})

    breadcrumbs.append({'name': book.name, 'url': None})  # Sách hiện tại
    print("breadcums:" ,breadcrumbs)


    related_books = dao.load_related_book(book)
    return render_template('details.html', related_books=related_books, book=book,breadcrumbs=breadcrumbs)

@app.route('/account')
def account():
    return render_template('account.html')

@app.route('/favourite')
def favourite():
    # query params = user.id, book.id
    return render_template('favourite.html')


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
            ORDER_BY_OPTIONS=ORDER_BY_OPTIONS
        )

@app.route('/order')
def order():
    return render_template('order.html')

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)

