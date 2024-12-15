from flask import redirect, request, url_for, render_template
from flask_admin.helpers import get_url
from markupsafe import Markup
from app import app, db, dao,utils
from flask_login import login_user, logout_user
from flask_admin import Admin, BaseView, expose, AdminIndexView
from app.models import Book, Review, Order, Voucher, Permission, Category, User
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, login_user
from app.models import Role


def _image_formatter(view, context, model, name):
    if getattr(model, name):
        return Markup(f'<img src="{model.image}" style="width: 50px; height: auto;">')
    return Markup('<span>No Image</span>')


def _truncate_formatter(view, context, model, name):
    text = getattr(model, name)  # Lấy giá trị từ model
    if text:
        truncated_text = ' '.join(text.split()[:10]) + ("..." if len(text.split()) > 10 else "")
        return truncated_text
    return ""


class AuthenticatedView(ModelView):
    def is_accessible(self):
        allowed_roles = ["Admin"]
        return current_user.is_authenticated and current_user.role.name in allowed_roles

    can_view_details = True
    can_export = True
    edit_modal = True
    details_modal = True
    page_size = 10
    can_export = True

    form_excluded_columns = ['created_at', 'updated_at']

#  "Admin", "Sales", "Storekeeper"
class AuthenticatedBaseView(BaseView):
    def is_accessible(self):
        allowed_roles = ["Admin"]
        return current_user.is_authenticated and current_user.role.name in allowed_roles

class LogoutView(AuthenticatedBaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.name in ["Admin", "Sales", "Storekeeper"]
    @expose("/")
    def index(self):
        logout_user()
        return redirect("/admin")


class StatsView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        return self.render('admin/stats.html')

class LapHoaDon(AuthenticatedBaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.name in ["Sales","Admin"]

    @expose("/")
    def index(self):
        return self.render('admin/laphoadon.html')

class LapPhieuNhap(AuthenticatedBaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.name in ["Storekeeper","Admin"]
    @expose("/")
    def index(self):
        data=dao.load_book()
        return self.render('admin/lapphieunhap.html',data =data )

class ThayDoiQuyDinh(AuthenticatedBaseView):
    @expose("/")
    def index(self):
        return self.render('admin/thaydoiquydinh.html')

class CategoryView(AuthenticatedView):
    column_formatters = {
        'image': _image_formatter,  # Áp dụng formatter vào cột "image"
    }
    column_list = ['id', 'name', 'image']
    column_filters = ['name']
    column_searchable_list = ['name']


class BookView(AuthenticatedView):
    column_formatters = {
        'description': _truncate_formatter,  # Áp dụng formatter vào cột "image"
        'image': _image_formatter,  # Áp dụng formatter vào cột "image"
    }
    column_list = ['id', 'name', 'image', 'standard_price', 'discount', 'unit_price', 'available_quantity',
                   'description','categories','publisher']
    form_create_rules = [
        'name',
        'standard_price',
        'unit_price',
        'is_enable',
        'image',
        'description',
        'publisher',
        'categories'
    ]

    form_edit_rules = [
        'name',
        'standard_price',
        'unit_price',
        'is_enable',
        'image',
        'description',
        'publisher',
        'categories'
    ]
    column_filters = ['name']
    column_searchable_list = ['name']



class ReviewView(AuthenticatedView):
    column_list = ['id','rating','comment']
    form_excluded_columns = ['user','created_at','updated_at']

class MyAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        stats = dao.count_product_by_cate()
        return self.render('admin/index.html', stats=stats)



admin = Admin(app=app, name="BookStore3H", template_mode="bootstrap4", index_view=MyAdminView())

admin.add_view(CategoryView(Category, db.session))
admin.add_view(BookView(Book, db.session))
admin.add_view(ReviewView(Review, db.session))
admin.add_view(ThayDoiQuyDinh(name="Quy Định"))
admin.add_view(LapHoaDon(name="Lập Hóa Đơn"))
admin.add_view(LapPhieuNhap(name="Lập Phiếu Nhập"))
admin.add_view(StatsView(name="Thống Kê"))
admin.add_view(LogoutView(name="Đăng Xuất"))
