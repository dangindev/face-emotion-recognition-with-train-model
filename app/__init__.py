# app/__init__.py
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager # Import LoginManager

app_instance = Flask(__name__)
app_instance.config.from_object(Config)

# Khởi tạo extensions
db = SQLAlchemy(app_instance)
login_manager = LoginManager(app_instance)
login_manager.login_view = 'login' # Tên của route xử lý đăng nhập (sẽ tạo ở routes.py)
login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
login_manager.login_message_category = 'info' # Category cho flash message (tùy chọn)


# Import routes và models sau khi các đối tượng được tạo
# Đảm bảo import models trước routes nếu routes có sử dụng models
from app import models # Uncomment dòng này
from app import routes