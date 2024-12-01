import math
from flask import render_template, request, redirect,session, jsonify
import dao
from app import app, login
from flask_login import login_user, logout_user
from flask_login import current_user


@app.route("/")
def index():
    page = request.args.get('page', 1)
    cate_id = request.args.get('category_id')
    kw = request.args.get('kw')
    prods = dao.load_new_products(cate_id=cate_id, kw=kw, page=int(page))

    banner = dao.load_banner()
    feature_books = dao.load_feature_book()
    cates = dao.load_categories()
    page_size = app.config["PAGE_SIZE"]
    total = dao.count_products()

    return render_template("index.html", banner=banner, feature_books=feature_books,
                           new_books=prods,
                           categories=cates, pages=math.ceil(total / page_size))


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
def login_abc():
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

@app.route("/logout")
def logout_process():
    logout_user()
    return redirect('/')

@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
