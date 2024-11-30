import math

from flask import render_template, request, redirect


import dao
from app import app
from flask_login import login_user, logout_user


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



    category_ids = dao.load_category_ids()
    return render_template("index.html", banner=banner, feature_books=feature_books,
                           new_books=prods,
                           category_ids=category_ids,

                           categories=cates, pages=math.ceil(total / page_size))


@app.route("/register", methods=['get', 'post'])
def register_view():
    err_msg = ''
    if request.method.__eq__('POST'):
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if not password.__eq__(confirm):
            err_msg = 'Mật khẩu không khớp!'
        else:
            data = request.form.copy()
            del data['confirm']
            avatar = request.files.get('avatar')
            dao.add_user(avatar=avatar, **data)

            return redirect('/login')

    return render_template('register.html', err_msg=err_msg)

@app.route("/login", methods=['get', 'post'])
def login_view():
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username=username, password=password)
        if user:
            login_user(user=user)
            return redirect('/')

    return render_template('login.html')

@app.route("/book_details")
def book_details():

    book_id = request.args.get('book_id')
    book = dao.load_book(book_id).first()

    category_ids = request.args.get('category_ids')
    relate_books = dao.load_relate_book(category_ids=category_ids)
    return render_template('book_details.html', relate_books=relate_books, category_ids=category_ids,book = book)

@app.route('/book_details_2')
def book_details_2():
    book = request.args.get('book.id')
    category_ids = request.args.get('category_ids')
    relate_books = dao.load_relate_book(category_ids=category_ids)
    return render_template('book_details_2.html', relate_books=relate_books, category_ids=category_ids, book=book)


if __name__ == '__main__':
    app.run(debug=True)
