# config.py
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ban-nen-thay-doi-key-nay'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ===> THÊM BIẾN CHỌN MODEL <===
    # Đặt tên file của model bạn muốn sử dụng mặc định ở đây.
    # Thay đổi giá trị này thành 'emotion_cnn_model_pretrained.h5' để dùng model kia.
    ACTIVE_EMOTION_MODEL_FILENAME = 'emotion_detection_model.h5'