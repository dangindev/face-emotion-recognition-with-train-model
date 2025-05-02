from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
# Nên import model User ở đây nếu cần validate trong form (vd: check username tồn tại)
# from app.models import User # Làm thế này có thể gây lỗi circular import, xem giải pháp bên dưới

class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(message="Vui lòng nhập tên đăng nhập."),
                                                    Length(min=3, max=64, message="Tên đăng nhập phải từ 3 đến 64 ký tự.")])
    password = PasswordField('Mật khẩu', validators=[DataRequired(message="Vui lòng nhập mật khẩu.")])
    remember_me = BooleanField('Ghi nhớ đăng nhập')
    submit = SubmitField('Đăng nhập')

class RegistrationForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(message="Địa chỉ email không hợp lệ.")])
    password = PasswordField('Mật khẩu', validators=[DataRequired(), Length(min=6, message="Mật khẩu phải có ít nhất 6 ký tự.")])
    password2 = PasswordField(
        'Nhập lại mật khẩu', validators=[DataRequired(),
                                       EqualTo('password', message='Mật khẩu nhập lại không khớp.')])
    submit = SubmitField('Đăng ký')

    # --- Custom Validators ---
    # Các hàm validate_<fieldname> sẽ tự động được gọi bởi WTForms

    def validate_username(self, username):
        # Import model User ngay bên trong hàm để tránh lỗi circular import
        from app.models import User
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            # Nếu tìm thấy user có username này rồi -> báo lỗi
            raise ValidationError('Tên đăng nhập này đã được sử dụng. Vui lòng chọn tên khác.')

    def validate_email(self, email):
        # Import model User ngay bên trong hàm
        from app.models import User
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Địa chỉ email này đã được sử dụng. Vui lòng chọn email khác.')