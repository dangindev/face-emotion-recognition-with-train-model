# run.py
from app import app_instance

if __name__ == '__main__':
    # Chạy app ở chế độ debug (tự động reload khi có thay đổi code)
    # Chỉ dùng debug=True cho development
    app_instance.run(debug=True)