from app import app_instance, db # Import thêm db
from flask import render_template, flash, redirect, url_for, request # Import thêm các hàm cần thiết
from app.models import User # Import model User
from flask_login import current_user, login_user, logout_user, login_required # Import các hàm/decorator của Flask-Login
from flask import request, jsonify 
import time 
import random 
from app.services import decode_image, detect_emotion_and_attention 
import traceback
from datetime import datetime
from flask import session 
from app.models import StudySession, EmotionLog, AttentionLog
import math
from collections import Counter
@app_instance.route('/')
@app_instance.route('/index')
@login_required # <<<=== YÊU CẦU ĐĂNG NHẬP
def index():
    # Dữ liệu mẫu cho dashboard (sẽ thay thế sau)
    return render_template('index.html', title='Dashboard')

@app_instance.route('/login', methods=['GET', 'POST'])
def login():
    # Nếu người dùng đã đăng nhập, chuyển hướng về trang index
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember_me') # Nếu có checkbox "Remember me"

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'danger') # Thông báo lỗi
            return redirect(url_for('login'))

        # Đăng nhập người dùng thành công
        login_user(user, remember=remember)
        flash(f'Chào mừng {user.username} quay trở lại!', 'success')

        # Chuyển hướng đến trang người dùng muốn truy cập trước đó (nếu có)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        return redirect(next_page)

    # Nếu là GET request, chỉ hiển thị form
    return render_template('login.html', title='Đăng nhập')

@app_instance.route('/logout')
def logout():
    logout_user()
    flash('Bạn đã đăng xuất.', 'info')
    return redirect(url_for('index')) # Chuyển về trang chủ (sẽ tự động qua login nếu index yêu cầu)

# === TẠM THỜI THÊM ROUTE ĐĂNG KÝ ĐƠN GIẢN ĐỂ TEST ===
# Trong ứng dụng thực tế cần form phức tạp hơn (Flask-WTF) và validation
@app_instance.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.', 'warning')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Tên đăng nhập đã tồn tại.', 'warning')
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Đăng ký')

@app_instance.route('/history')
@login_required
def history():
    """
    Retrieves study sessions and their statistics for the current user
    and renders the history page.
    """
    print(f"[*] User {current_user.id} requested history page.")
    processed_sessions = [] # List để chứa dữ liệu đã xử lý của các session

    try:
        # 1. Lấy tất cả các session của user hiện tại, sắp xếp mới nhất lên đầu
        user_sessions = StudySession.query.filter_by(user_id=current_user.id)\
                                          .order_by(StudySession.start_time.desc())\
                                          .all()

        print(f"[*] Found {len(user_sessions)} sessions for user {current_user.id}.")

        # 2. Xử lý từng session
        for session_entry in user_sessions:
            session_data = {
                'id': session_entry.id,
                'start_time': session_entry.start_time,
                'end_time': session_entry.end_time,
                'duration_str': "N/A",
                'attention_percentage': 0.0,
                'emotion_counts': {},
                'most_common_emotion': "N/A",
                'emotion_chart_data': {'labels': [], 'data': []} # Chuẩn bị cho biểu đồ
            }

            # Tính thời lượng nếu session đã kết thúc
            if session_entry.end_time and session_entry.start_time:
                duration_td = session_entry.end_time - session_entry.start_time
                total_seconds = duration_td.total_seconds()
                if total_seconds < 60:
                    session_data['duration_str'] = f"{math.ceil(total_seconds)} giây" 
                elif total_seconds < 3600:
                    session_data['duration_str'] = f"{math.ceil(total_seconds / 60)} phút" 
                else:
                     hours = int(total_seconds // 3600)
                     minutes = int((total_seconds % 3600) // 60)
                     session_data['duration_str'] = f"{hours} giờ {minutes} phút"


            # Lấy tất cả các bản ghi log của session này
            attention_logs = AttentionLog.query.filter_by(session_id=session_entry.id).all()
            emotion_logs = EmotionLog.query.filter_by(session_id=session_entry.id).all()

            # Tính tỷ lệ tập trung
            if attention_logs: # Chỉ tính nếu có log
                total_logs = len(attention_logs)
                attentive_count = sum(1 for log in attention_logs if log.is_attentive)
                session_data['attention_percentage'] = round((attentive_count / total_logs) * 100, 1) if total_logs > 0 else 0.0

            # Đếm cảm xúc và chuẩn bị dữ liệu biểu đồ
            if emotion_logs:
                # Lọc bỏ các trạng thái không phải cảm xúc thực sự (ví dụ)
                valid_emotions = [log.emotion for log in emotion_logs if log.emotion not in ["No face detected", "N/A", "Error"]]
                if valid_emotions:
                    emotion_counter = Counter(valid_emotions)
                    session_data['emotion_counts'] = dict(emotion_counter)
                    # Tìm cảm xúc phổ biến nhất
                    most_common = emotion_counter.most_common(1)
                    if most_common:
                         session_data['most_common_emotion'] = most_common[0][0]

                    # Dữ liệu cho biểu đồ (Chart.js)
                    chart_labels = list(emotion_counter.keys())
                    chart_data = list(emotion_counter.values())
                    session_data['emotion_chart_data'] = {'labels': chart_labels, 'data': chart_data}
                else:
                    session_data['most_common_emotion'] = "Không có dữ liệu cảm xúc"


            processed_sessions.append(session_data) # Thêm session đã xử lý vào list

    except Exception as e:
        print(f"[!] ERROR retrieving or processing history for user {current_user.id}: {e}")
        traceback.print_exc()
        flash("Đã xảy ra lỗi khi tải lịch sử học tập.", "danger")
        # Trả về template rỗng hoặc có thông báo lỗi

    return render_template('history.html',
                           title='Lịch sử học tập',
                           sessions=processed_sessions) # Truyền list session đã xử lý vào template


# === HÀM PROCESS_FRAME ĐÃ CẬP NHẬT HOÀN CHỈNH ===
@app_instance.route('/process_frame', methods=['POST'])
@login_required
def process_frame():
    """
    Receives image/model ID, processes AI, LOGS results (including 'No face'),
    and returns results to frontend.
    """
    processing_start_time = time.time()
    try:
        # 1. Lấy session ID và dữ liệu request
        current_session_id = session.get('current_study_session_id')
        if current_session_id is None:
            print("[/process_frame] Warning: No active session ID found. Skipping DB logging.")
            # Vẫn tiếp tục xử lý để trả kết quả về UI

        data = request.get_json()
        if not data or 'image_data' not in data or 'selected_model' not in data:
            print("[/process_frame] Error: Missing required data (image_data or selected_model).")
            return jsonify({'error': 'Missing required data'}), 400

        image_base64 = data['image_data']
        selected_model_id = data['selected_model']

        # 2. Decode ảnh
        image_cv2 = decode_image(image_base64)
        if image_cv2 is None:
            print("[/process_frame] Error: Failed decoding image.")
            return jsonify({'error': 'Failed to decode image'}), 400

        # 3. Gọi hàm xử lý AI
        emotion_result, attention_result_raw = detect_emotion_and_attention(
            image_cv2, requested_model_id=selected_model_id
        )
        attention_result = bool(attention_result_raw) # Ép kiểu bool

        # ========== LƯU LOG VÀO DATABASE (Cập nhật logic) ==========
        log_saved = False
        if current_session_id is not None:
            # ===> LOGIC MỚI: Log cả "No face", chỉ bỏ qua lỗi thực sự <===
            is_loggable_result = not emotion_result.lower().startswith('error') and \
                                 emotion_result != 'N/A' and \
                                 'not loaded' not in emotion_result.lower() and \
                                 'unavailable' not in emotion_result.lower()
            # 'No face detected' giờ sẽ là True trong is_loggable_result

            if is_loggable_result:
                try:
                    timestamp_now = datetime.utcnow()
                    # Tạo bản ghi EmotionLog (Lưu cả 'No face detected')
                    emotion_log_entry = EmotionLog(
                        session_id=current_session_id,
                        timestamp=timestamp_now,
                        emotion=emotion_result # Sẽ là 'No face detected' nếu không thấy mặt
                    )
                    db.session.add(emotion_log_entry)

                    # Tạo bản ghi AttentionLog (sẽ là False nếu không thấy mặt)
                    attention_log_entry = AttentionLog(
                        session_id=current_session_id,
                        timestamp=timestamp_now,
                        is_attentive=attention_result
                    )
                    db.session.add(attention_log_entry)

                    db.session.commit() # Lưu vào DB
                    log_saved = True
                    # ===> THÊM LOG XÁC NHẬN LƯU <===
                    print(f"   [Log OK] Session {current_session_id}: Saved E='{emotion_result}', A={attention_result}")

                except Exception as log_error:
                    db.session.rollback()
                    print(f"[!!!] ERROR saving logs to DB for session {current_session_id}: {log_error}")
            # else: # Dùng để debug tại sao không log
                 # print(f"   [Log Skip] Session {current_session_id}: Invalid result for logging (E='{emotion_result}')")
        # ============================================================

        processing_end_time = time.time()
        total_processing_time_ms = round((processing_end_time - processing_start_time) * 1000)

        # 4. Trả kết quả về frontend
        return jsonify({
            'emotion': emotion_result,
            'attention': attention_result,
            'processing_time_ms': total_processing_time_ms
        })

    except Exception as e:
        # Bắt lỗi không mong muốn trong khối try
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"CRITICAL UNHANDLED ERROR in /process_frame: {type(e).__name__}")
        traceback.print_exc()
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return jsonify({'error': f'Internal Server Error: {type(e).__name__}'}), 500

    

# API endpoint để BẮT ĐẦU một phiên học mới
@app_instance.route('/start_session', methods=['POST'])
@login_required
def start_session():
    """
    Creates a new StudySession record when the webcam starts.
    Stores the new session ID in the Flask session.
    """
    try:
        # Tạo bản ghi session mới
        new_session = StudySession(
            user_id=current_user.id,
            start_time=datetime.utcnow() # Thời gian UTC hiện tại
            # end_time sẽ là None ban đầu
        )
        db.session.add(new_session)
        db.session.commit() # Lưu vào DB để lấy ID

        # Lưu ID của session vừa tạo vào Flask session (cookie-based)
        # Key này sẽ được dùng bởi /process_frame và /stop_session
        session['current_study_session_id'] = new_session.id

        print(f"[*] User {current_user.id} started session {new_session.id}")
        return jsonify({
            'message': 'Session started successfully',
            'session_id': new_session.id # Trả về ID để JS có thể debug nếu cần
        }), 201 # 201 Created

    except Exception as e:
        db.session.rollback() # Hoàn tác nếu có lỗi DB
        print(f"[!] ERROR in /start_session for user {current_user.id}: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to start session'}), 500
    
# API endpoint để KẾT THÚC phiên học
@app_instance.route('/stop_session', methods=['POST'])
@login_required
def stop_session():
    """
    Updates the end_time for the current StudySession record.
    Removes the session ID from the Flask session.
    """
    # Lấy session ID từ Flask session
    current_session_id = session.get('current_study_session_id')

    if current_session_id is None:
        print(f"[*] User {current_user.id} requested to stop session, but no active session ID found.")
        # Không có session đang hoạt động để dừng, có thể bỏ qua hoặc trả lỗi nhẹ
        return jsonify({'message': 'No active session to stop.'}), 200 # Hoặc 404

    try:
        # Tìm session tương ứng trong DB
        study_session = StudySession.query.get(current_session_id)

        if study_session is None:
            print(f"[!] Warning: Active session ID {current_session_id} in Flask session, but not found in DB.")
             # Xóa session ID khỏi Flask session để tránh lỗi sau này
            session.pop('current_study_session_id', None)
            return jsonify({'error': 'Session inconsistency detected.'}), 500
        elif study_session.user_id != current_user.id:
             print(f"[!] SECURITY WARNING: User {current_user.id} tried to stop session {current_session_id} belonging to user {study_session.user_id}.")
             # Xóa session ID để tránh lạm dụng
             session.pop('current_study_session_id', None)
             return jsonify({'error': 'Permission denied'}), 403


        # Cập nhật thời gian kết thúc
        study_session.end_time = datetime.utcnow()
        db.session.add(study_session) # Add lại để SQLAlchemy biết có thay đổi
        db.session.commit()

        print(f"[*] User {current_user.id} stopped session {current_session_id}")

        # Xóa session ID khỏi Flask session sau khi đã xử lý xong
        session.pop('current_study_session_id', None)

        return jsonify({'message': 'Session stopped and updated successfully.'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[!] ERROR in /stop_session for session {current_session_id}: {e}")
        traceback.print_exc()
        # Không xóa session ID nếu lỗi để có thể thử lại? Tùy logic mong muốn.
        return jsonify({'error': 'Failed to stop session'}), 500