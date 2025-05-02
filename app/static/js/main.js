// app/static/js/main.js

// Biến toàn cục để lưu luồng video và interval ID
let videoStream = null;
let intervalId = null;
const CAPTURE_INTERVAL = 1500; // Chụp ảnh mỗi 1.5 giây (1500 ms)

// Lấy các phần tử DOM cần thiết
document.addEventListener('DOMContentLoaded', (event) => {
    const videoElement = document.getElementById('webcamVideo');
    const canvasElement = document.getElementById('canvas');
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const webcamArea = document.getElementById('webcam-area');
    const statusElement = document.getElementById('status');
    const emotionElement = document.getElementById('current-emotion');
    const attentionElement = document.getElementById('current-attention');
    // Lấy thẻ select model
    const modelSelectElement = document.getElementById('modelSelect');
    // Lấy cả khu vực chứa select để ẩn/hiện
    const modelSelectorArea = document.getElementById('model-selector-area');

    // Kiểm tra các Element có tồn tại không
    if (!videoElement || !canvasElement || !startButton || !stopButton || !webcamArea || !statusElement || !emotionElement || !attentionElement || !modelSelectElement || !modelSelectorArea) {
        console.error("JS Error: Một hoặc nhiều phần tử DOM cần thiết không tìm thấy trên trang này!");
        // Không return vội, có thể đang ở trang khác
        if (window.location.pathname !== '/' && window.location.pathname !== '/index') {
             return; // Chỉ thoát nếu không phải trang index
        }
        if (!modelSelectElement) console.error("Element #modelSelect not found!"); // Log cụ thể lỗi thiếu
    }

    // Hàm cập nhật trạng thái UI
    function updateStatus(message, type = 'secondary') {
        if (statusElement) {
             statusElement.textContent = message;
             statusElement.className = `badge bg-${type}`;
        }
    }

    // Hàm cập nhật kết quả cảm xúc/tập trung UI
    function updateResults(emotion = '...', attention = '...') {
         if (emotionElement && attentionElement) {
              const attentionText = typeof attention === 'boolean' ? (attention ? 'Tập trung' : 'Không tập trung') : '...';
              const attentionBadge = typeof attention === 'boolean' ? (attention ? 'success' : 'warning') : 'primary';
              emotionElement.textContent = emotion;
              attentionElement.textContent = attentionText;
              emotionElement.className = `badge bg-info`;
              attentionElement.className = `badge bg-${attentionBadge}`;
         }
    }

    // ---- Hàm Bật Webcam ----
    async function startWebcam() {
        // ... (code ẩn/hiện nút và selector) ...
        updateStatus("Đang khởi tạo...", "warning");

        // <<< GỌI API BẮT ĐẦU SESSION >>>
        try {
            console.log("Calling /start_session API...");
            const startResponse = await fetch('/start_session', { method: 'POST' });
            if (!startResponse.ok) {
                 console.error("Failed to start session on backend:", startResponse.status, await startResponse.text());
                 throw new Error("Backend couldn't start session."); // Ném lỗi để bắt ở dưới
            }
            const startData = await startResponse.json();
            console.log("Backend session started:", startData); // Log session ID từ backend
            // Nếu thành công thì mới tiếp tục bật webcam
        } catch (startError) {
            console.error('Error starting session:', startError);
            updateStatus("Lỗi bắt đầu phiên", "danger");
            modelSelectorArea.style.display = 'block'; // Hiện lại lựa chọn
            startButton.disabled = false;
            stopButton.disabled = true;
            alert("Không thể bắt đầu phiên học trên máy chủ. Vui lòng thử lại.");
            return; // << Dừng hàm nếu không start session được
        }
        // <<< KẾT THÚC GỌI API >>>


        try {
            // ... (getUserMedia, gán srcObject) ...
            videoStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            if (videoElement) videoElement.srcObject = videoStream;
            if (webcamArea) webcamArea.style.display = 'block';
            console.log("Webcam stream started.");
            updateStatus("Đang hoạt động", "success");
            stopButton.disabled = false; // Kích hoạt nút stop SAU KHI MỌI THỨ OK

            // Bắt đầu chụp frame
            if (intervalId) clearInterval(intervalId);
            intervalId = setInterval(captureAndSendFrame, CAPTURE_INTERVAL);
            console.log("Frame capture interval started.");

        } catch (error) {
            // ... (xử lý lỗi getUserMedia) ...
        }
    }

    // ---- Hàm Tắt Webcam ----
    function stopWebcam() {
        // ... (dừng interval, dừng stream video) ...
         console.log("Stopping webcam...");
        if (intervalId) {clearInterval(intervalId); intervalId = null;}
        if (videoStream) {videoStream.getTracks().forEach(track => track.stop()); videoStream = null;}
        if (videoElement) videoElement.srcObject = null;

        // Cập nhật UI
        if (webcamArea) webcamArea.style.display = 'none';
        updateStatus("Đã tắt", "secondary");
        updateResults('...', '...');
        if (modelSelectorArea) modelSelectorArea.style.display = 'block';
        if (startButton) startButton.disabled = false;
        if (stopButton) stopButton.disabled = true;

        // <<< GỌI API KẾT THÚC SESSION >>>
        console.log("Calling /stop_session API...");
        fetch('/stop_session', { method: 'POST' })
           .then(response => {
               if (!response.ok) {
                   console.error("Failed to stop session on backend:", response.status);
               }
               return response.json(); // Vẫn parse json để xem message
           })
           .then(data => {
               console.log('Backend session stopped response:', data);
               // Có thể thêm thông báo nhẹ cho user nếu cần
           })
           .catch(error => {
               console.error('Error stopping session:', error);
               // Thông báo lỗi nhẹ nếu cần
           });
        // <<< KẾT THÚC GỌI API >>>
    }

    // ---- Hàm Chụp và Gửi Frame ----
    async function captureAndSendFrame() {
        if (!videoStream || !canvasElement || !modelSelectElement) {
            console.warn("captureAndSendFrame: stream, canvas, or modelSelect not ready.");
            return; // Dừng nếu chưa sẵn sàng
        }

        // Lấy context và vẽ ảnh
        const context = canvasElement.getContext('2d');
        if (!context) {
             console.error("Could not get canvas context");
             return;
        }
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;
        if (canvasElement.width === 0 || canvasElement.height === 0) {
             console.warn("captureAndSendFrame: video dimensions are zero.");
             return; // Bỏ qua frame nếu video chưa có kích thước
        }
        context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);

        // Chuyển ảnh sang base64
        let imageDataBase64;
        try {
            imageDataBase64 = canvasElement.toDataURL('image/jpeg', 0.8);
        } catch (e) {
            console.error("Error converting canvas to DataURL:", e);
            return;
        }

        // Lấy giá trị model đang được chọn
        const selectedModel = modelSelectElement.value;
        // console.log(`[Frame] Using model: ${selectedModel}, Image size: ${Math.round(imageDataBase64.length / 1024)} KB`); // Debug

        // Kiểm tra giá trị hợp lệ trước khi gửi
        if (!selectedModel || !imageDataBase64 || imageDataBase64.length < 100) { // Thêm kiểm tra độ dài base64
            console.error("ERROR: Missing selectedModel or invalid imageData before sending!");
            return;
        }

        // Gửi dữ liệu lên backend
        try {
            const response = await fetch('/process_frame', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Thêm CSRF token nếu dùng Flask-WTF sau này
                },
                body: JSON.stringify({
                    image_data: imageDataBase64,
                    selected_model: selectedModel // << GỬI ID MODEL ĐÃ CHỌN
                })
            });

            // Xử lý response
            if (!response.ok) {
                 const errorText = await response.text(); // Lấy nội dung lỗi từ server
                 console.error(`Server error: ${response.status} ${response.statusText}`, errorText);
                 updateStatus(`Lỗi Server (${response.status})`, "danger");
                 // Có thể dừng webcam nếu lỗi nghiêm trọng lặp lại
                 // if (response.status >= 500) stopWebcam();
                 return; // Dừng xử lý frame này
            }

            const result = await response.json();
            // console.log("Result received:", result);
            updateResults(result.emotion, result.attention); // Cập nhật UI

        } catch (error) {
            console.error('Network or fetch error:', error);
            updateStatus(`Lỗi Mạng`, "danger");
            // Cân nhắc dừng webcam nếu mạng lỗi liên tục
            // stopWebcam();
        }
    }

    // Gán sự kiện cho các nút chỉ khi các nút tồn tại
    if(startButton && stopButton) {
         startButton.addEventListener('click', startWebcam);
         stopButton.addEventListener('click', stopWebcam);
         console.log("Event listeners attached to buttons.");
    } else {
         console.warn("Start/Stop buttons not found on this page, listeners not attached.");
    }

}); // Kết thúc DOMContentLoaded

console.log("main.js loaded and ready.");