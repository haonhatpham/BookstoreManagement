from flask import redirect, request, url_for, render_template,flash
from flask_admin.helpers import get_url
from markupsafe import Markup
from app import app, db, dao,utils
from flask_login import login_user, logout_user
from flask_admin import Admin, BaseView, expose, AdminIndexView
from app.models import Book, Review, Order, Voucher, Permission, Category, User,Configuration
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, login_user
from app.models import Role
import calendar


def _image_formatter(view, context, model, name):
    # Kiểm tra nếu thuộc tính `name` có giá trị
    if getattr(model, name):
        return Markup(f'<img src="{getattr(model, name)}" style="width: 50px; height: auto;">')
    # Nếu không có `name`, kiểm tra `avata_file`
    if getattr(model, 'avatar_file'):
        return Markup(f'<img src="{model.avatar_file}" style="width: 50px; height: auto;">')
    # Trả về nếu không có hình ảnh
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
        allowed_roles = ["Admin"]
        return current_user.is_authenticated and current_user.role.name in allowed_roles

    can_view_details = True
    can_export = True
    edit_modal = True
    details_modal = True
    page_size = 10
    can_export = True

    form_excluded_columns = ['created_at', 'updated_at']

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
    @expose("/")
    def index(self):
        labels = []
        for i in range(1, 13):
            labels.append(calendar.month_name[i])
        data = utils.statistic_revenue()

        return self.render('admin/chart.html', data=data, labels=labels)

class LapHoaDon(AuthenticatedBaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.name in ["Sales","Admin"]

    @expose("/")
    def index(self):
        data=dao.load_book()
        user=dao.load_User()
        return self.render('admin/laphoadon.html',data=data, user=user)


class LapPhieuNhap(AuthenticatedBaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.name in ["Storekeeper","Admin"]
    @expose("/")
    def index(self):
        data=dao.load_book()
        min_import_quantity,max_stock_for_import=dao.get_import_rules()
        return self.render('admin/lapphieunhap.html',data =data ,min_import_quantity=min_import_quantity
                           ,max_stock_for_import=max_stock_for_import)

class PhanQuyen(AuthenticatedBaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.name in ["Admin"]
    @expose("/")
    def index(self):
        permission=dao.load_permission()
        role=dao.load_role()
        user=dao.load_user()
        return self.render('admin/phanquyen.html',permission=permission,user=user,role=role)

class ThayDoiQuyDinh(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    page_size = 20
    can_view_details = True
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.name == "Admin"



class CategoryView(AuthenticatedView):
    column_formatters = {
        'image': _image_formatter,  # Áp dụng formatter vào cột "image"
    }
    column_list = ['id', 'name', 'image']


class BookView(AuthenticatedView):
    column_formatters = {
        'description': _truncate_formatter,  # Áp dụng formatter vào cột "description"
        'image': _image_formatter,  # Áp dụng formatter vào cột "image"
    }
    column_list = ['id', 'name', 'image', 'standard_price', 'discount', 'unit_price', 'available_quantity',
                   'description','categories','publisher']
    form_create_rules = [
        'name','standard_price','unit_price','is_enable','image','description','publisher','categories']
    form_edit_rules = [
        'name','standard_price','unit_price','is_enable','image','description','publisher','categories']
    column_filters = ['name']
    column_searchable_list = ['name']


class UserView(AuthenticatedView):
    column_formatters = {
        'avatar_file': _image_formatter,  # Áp dụng formatter vào cột "image"
    }
    column_list = ['id', 'first_name','last_name','email','phone','birth','gender','avatar_file',
                   'active']

    form_create_rules = [
        'first_name', 'last_name', 'email', 'phone', 'birth', 'gender', 'avatar_file', 'active']
    form_edit_rules = [
        'first_name', 'last_name', 'email', 'phone', 'birth', 'gender', 'avatar_file', 'active']

class ReviewView(AuthenticatedView):
    column_list = ['id','rating','comment']
    form_excluded_columns = ['user','created_at','updated_at']

class MyAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        stats = dao.count_product_by_cate()
        return self.render('admin/index.html', stats=stats)

class OrderView(AuthenticatedView):
    column_sortable_list = ['initiated_date']


class OrderView(AuthenticatedView):
    column_sortable_list = ['initiated_date', 'total_payment']
    column_list = ['id','total_payment','received_money','paid_date','delivered_date'
        ,'payment_method_id']
    form_create_rules =['id', 'initiated_date', 'cancel_date','total_payment','received_money','paid_date','delivered_date'
        ,'payment_method_id']
    form_edit_rules = ['id', 'initiated_date', 'cancel_date','total_payment','received_money','paid_date','delivered_date'
        ,'payment_method_id']



admin = Admin(app=app, name="BookStore3H", template_mode="bootstrap4", index_view=MyAdminView())
admin.add_view(CategoryView(Category, db.session))
admin.add_view(BookView(Book, db.session))
admin.add_view(OrderView(Order, db.session))
admin.add_view(ReviewView(Review, db.session))
admin.add_view(UserView(User, db.session))
admin.add_view(ThayDoiQuyDinh(Configuration, db.session))
admin.add_view(PhanQuyen(name="Phân Quyền"))
admin.add_view(LapHoaDon(name="Lập Hóa Đơn"))
admin.add_view(LapPhieuNhap(name="Lập Phiếu Nhập"))
admin.add_view(StatsView(name="Thống Kê"))
admin.add_view(LogoutView(name="Đăng Xuất"))

