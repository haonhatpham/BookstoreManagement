from flask import redirect, request, url_for, render_template
from flask_admin.helpers import get_url
from markupsafe import Markup
from app import app, db, dao
from flask_login import login_user, logout_user
from flask_admin import Admin, BaseView, expose, AdminIndexView
from app.models import Book, Review, Order, Voucher, Permission, Category, User
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, login_user
from app.models import Role


def _image_formatter(view, context, model, name):
    if getattr(model, name):  # Kiểm tra nếu có hình ảnh
        return Markup(f'<img src="{model.image}" style="width: 50px; height: auto;">')
    return Markup('<span>No Image</span>')


def _truncate_formatter(view, context, model, name):
    text = getattr(model, name)  # Lấy giá trị từ model
    if text:
        # Lấy 10 từ đầu tiên và thêm "..." nếu có nhiều hơn
        truncated_text = ' '.join(text.split()[:10]) + ("..." if len(text.split()) > 10 else "")
        return truncated_text
    return ""


class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.name == "Admin"

    can_view_details = True
    can_export = True
    edit_modal = True
    details_modal = True
    page_size = 10
    column_filters = ['name']
    can_export = True
    column_searchable_list = ['name']


class AuthenticatedBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.name == "Admin"


class LogoutView(AuthenticatedBaseView):
    @expose("/")
    def index(self):
        logout_user()
        return redirect("/admin")


class StatsView(AuthenticatedBaseView):
    @expose("/")
    def index(self):
        stats = dao.stats_revenue(kw=request.args.get('kw'))
        return self.render('admin/stats.html')

class LapHoaDon(AuthenticatedBaseView):
    @expose("/")
    def index(self):
        stats = dao.stats_revenue(kw=request.args.get('kw'))
        return self.render('admin/laphoadon.html')

class LapPhieuNhap(AuthenticatedBaseView):
    @expose("/")
    def index(self):
        stats = dao.stats_revenue(kw=request.args.get('kw'))
        return self.render('admin/lapphieunhap.html')

class ThayDoiQuyDinh(AuthenticatedBaseView):
    @expose("/")
    def index(self):
        stats = dao.stats_revenue(kw=request.args.get('kw'))
        return self.render('admin/thaydoiquydinh.html')

class CategoryView(AuthenticatedView):
    column_formatters = {
        'image': _image_formatter,  # Áp dụng formatter vào cột "image"
    }
    column_list = ['id', 'name', 'image']


class BookView(AuthenticatedView):
    column_formatters = {
        'description': _truncate_formatter,  # Áp dụng formatter vào cột "image"
        'image': _image_formatter,  # Áp dụng formatter vào cột "image"
    }
    column_list = ['id', 'name', 'image', 'standard_price', 'discount', 'unit_price', 'available_quantity',
                   'description',
                   'is_enable']


class MyAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        stats = dao.count_product_by_cate()
        return self.render('admin/index.html', stats=stats)


admin = Admin(app=app, name="BookStore3H", template_mode="bootstrap4", index_view=MyAdminView())
admin.add_view(CategoryView(Category, db.session))
admin.add_view(BookView(Book, db.session))
admin.add_view(ThayDoiQuyDinh(name="Quy Định"))
admin.add_view(LapHoaDon(name="Lập Hóa Đơn"))
admin.add_view(LapPhieuNhap(name="Lập Phiếu Nhập"))
admin.add_view(StatsView(name="Thống Kê"))
admin.add_view(LogoutView(name="Đăng Xuất"))
