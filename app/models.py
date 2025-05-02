# app/models.py
from app import db, login_manager # Import db và login_manager từ __init__.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin # Import UserMixin

# Hàm user_loader bắt buộc cho Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Kế thừa UserMixin để tích hợp với Flask-Login
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    # Quan hệ ngược lại với StudySession
    sessions = db.relationship('StudySession', backref='student', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self): # Phương thức hiển thị khi print đối tượng User
        return f'<User {self.username}>'

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Khóa ngoại liên kết tới User
    start_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    # Quan hệ ngược lại với EmotionLog và AttentionLog
    emotion_logs = db.relationship('EmotionLog', backref='session', lazy='dynamic')
    attention_logs = db.relationship('AttentionLog', backref='session', lazy='dynamic')

    def __repr__(self):
        return f'<Session {self.id} by User {self.user_id}>'

class EmotionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('study_session.id'), nullable=False) # Khóa ngoại
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    emotion = db.Column(db.String(64)) # Ví dụ: 'happy', 'sad', 'neutral'
    confidence = db.Column(db.Float) # Độ tin cậy (nếu model cung cấp)

    def __repr__(self):
        return f'<EmotionLog {self.id} for Session {self.session_id}: {self.emotion}>'

class AttentionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('study_session.id'), nullable=False) # Khóa ngoại
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_attentive = db.Column(db.Boolean) # True nếu tập trung, False nếu không

    def __repr__(self):
        return f'<AttentionLog {self.id} for Session {self.session_id}: Attentive={self.is_attentive}>'