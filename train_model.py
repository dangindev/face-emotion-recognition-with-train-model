# train_model.py (Version for Image Folder Dataset)
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D, BatchNormalization, Activation, Rescaling
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import CategoricalCrossentropy
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import matplotlib.pyplot as plt
import os
import numpy as np

# --- Configuration ---
# >> CẬP NHẬT ĐƯỜNG DẪN DATASET <<
DATASET_DIR = 'dataset' # Thư mục chứa 'train' và 'test'
TRAIN_DIR = os.path.join(DATASET_DIR, 'train')
TEST_DIR = os.path.join(DATASET_DIR, 'test') # Sẽ dùng tập test làm validation

MODEL_SAVE_PATH = 'emotion_cnn_model.h5' # Tên file model sẽ lưu ra
IMG_WIDTH, IMG_HEIGHT = 48, 48     # Kích thước ảnh mong muốn (FER2013 gốc là 48x48)
NUM_CLASSES = 7                    # Số lớp cảm xúc (thường là 7 cho FER2013)
BATCH_SIZE = 64                    # Số lượng ảnh xử lý trong 1 lần train step
EPOCHS = 60                        # Số lượt duyệt qua toàn bộ tập huấn luyện
COLOR_MODE = 'grayscale'           # 'grayscale' hoặc 'rgb'
CHANNELS = 1 if COLOR_MODE == 'grayscale' else 3 # Số kênh màu

# --- 1. Load Data using image_dataset_from_directory ---
print(f"[*] Loading datasets from directories...")
print(f"    Train directory: {os.path.abspath(TRAIN_DIR)}")
print(f"    Validation directory: {os.path.abspath(TEST_DIR)}")

# Kiểm tra xem thư mục có tồn tại không
if not os.path.isdir(TRAIN_DIR) or not os.path.isdir(TEST_DIR):
    print(f"[!] ERROR: Train or Test directory not found.")
    print(f"[!] Please ensure the 'dataset' folder exists in the project root and contains 'train' and 'test' subfolders.")
    exit()

# Tạo dataset huấn luyện
try:
    train_dataset = tf.keras.utils.image_dataset_from_directory(
        TRAIN_DIR,
        labels='inferred',          # Tự suy ra nhãn từ tên thư mục con
        label_mode='categorical',   # Nhãn dạng one-hot encoding
        image_size=(IMG_WIDTH, IMG_HEIGHT),
        interpolation='nearest',    # Phương pháp resize
        batch_size=BATCH_SIZE,
        color_mode=COLOR_MODE,      # Đọc ảnh dạng grayscale hoặc rgb
        shuffle=True                # Xáo trộn dữ liệu huấn luyện
    )
except Exception as e:
    print(f"[!] ERROR: Failed to create training dataset. Error: {e}")
    print(f"[!] Check if '{TRAIN_DIR}' contains subdirectories for each emotion class.")
    exit()

# Tạo dataset validation (dùng tập test làm validation)
try:
    val_dataset = tf.keras.utils.image_dataset_from_directory(
        TEST_DIR,
        labels='inferred',
        label_mode='categorical',
        image_size=(IMG_WIDTH, IMG_HEIGHT),
        interpolation='nearest',
        batch_size=BATCH_SIZE,
        color_mode=COLOR_MODE,
        shuffle=False               # Không cần xáo trộn validation/test set
    )
except Exception as e:
     print(f"[!] ERROR: Failed to create validation dataset. Error: {e}")
     print(f"[!] Check if '{TEST_DIR}' contains subdirectories for each emotion class.")
     exit()


# Lấy tên các lớp cảm xúc (thứ tự thường theo alphabet)
class_names = train_dataset.class_names
print(f"[*] Found emotion classes: {class_names}")
# >> QUAN TRỌNG: Kiểm tra xem số lớp và tên lớp có khớp với NUM_CLASSES và EMOTION_LABELS bạn dùng ở Bước 4 không.
# Nếu thứ tự khác (ví dụ không phải là ['angry', 'disgust', ... 'neutral']), bạn cần cập nhật EMOTION_LABELS trong services.py cho đúng! <<
if len(class_names) != NUM_CLASSES:
    print(f"[!] WARNING: Found {len(class_names)} classes, but NUM_CLASSES is set to {NUM_CLASSES}. Check your dataset folders or configuration.")
    # Cập nhật lại NUM_CLASSES nếu cần
    # NUM_CLASSES = len(class_names)

# --- 2. Optimize Datasets for Performance (Optional but Recommended) ---
AUTOTUNE = tf.data.AUTOTUNE
train_dataset = train_dataset.cache().prefetch(buffer_size=AUTOTUNE)
val_dataset = val_dataset.cache().prefetch(buffer_size=AUTOTUNE)
print("[*] Datasets optimized with cache() and prefetch().")

# --- 3. Build CNN Model Architecture ---
print("[*] Building CNN model...")
model = Sequential(name='EmotionCNN_FromFolders')

# Thêm lớp Rescaling để chuẩn hóa pixel (thay vì làm thủ công)
model.add(Rescaling(1./255, input_shape=(IMG_WIDTH, IMG_HEIGHT, CHANNELS)))

# --- Các lớp CNN giữ nguyên như trước ---
# Block 1
model.add(Conv2D(32, (3, 3), padding='same', kernel_initializer='he_normal'))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(Conv2D(32, (3, 3), padding='same', kernel_initializer='he_normal'))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

# Block 2
model.add(Conv2D(64, (3, 3), padding='same', kernel_initializer='he_normal'))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(Conv2D(64, (3, 3), padding='same', kernel_initializer='he_normal'))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

# Block 3
model.add(Conv2D(128, (3, 3), padding='same', kernel_initializer='he_normal'))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(Conv2D(128, (3, 3), padding='same', kernel_initializer='he_normal'))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

# Flatten và Dense Layers
model.add(Flatten())
model.add(Dense(64, kernel_initializer='he_normal'))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(Dropout(0.5))

model.add(Dense(NUM_CLASSES, kernel_initializer='he_normal', activation='softmax')) # Output layer
# -----------------------------------------

print("[*] Model built successfully.")
model.summary() # In cấu trúc model

# --- 4. Compile Model ---
print("[*] Compiling model...")
model.compile(loss=CategoricalCrossentropy(),
              optimizer=Adam(learning_rate=0.001),
              metrics=['accuracy'])
print("[*] Model compiled.")

# --- 5. Define Callbacks ---
print("[*] Setting up callbacks...")
# Dừng sớm nếu validation loss không cải thiện sau 'patience' epochs
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=1)
# Lưu lại model tốt nhất (dựa trên validation accuracy) vào file
model_checkpoint = ModelCheckpoint(MODEL_SAVE_PATH, monitor='val_accuracy', save_best_only=True, verbose=1)
# Giảm learning rate nếu không có cải thiện
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=0.00001, verbose=1)
callbacks = [early_stopping, model_checkpoint, reduce_lr]
print("[*] Callbacks ready.")

# --- 6. Train the Model ---
print(f"[*] Starting training for {EPOCHS} epochs...")
# Sử dụng trực tiếp tf.data.Dataset objects
history = model.fit(
    train_dataset,                  # Dữ liệu huấn luyện
    epochs=EPOCHS,
    validation_data=val_dataset,    # Dữ liệu validation
    callbacks=callbacks,
    verbose=1
)
print("[*] Training finished.")

# --- 7. Evaluate and Plot (Optional) ---
print("[*] Evaluating best model on validation set...")
# Model đã restore trọng số tốt nhất do EarlyStopping(restore_best_weights=True)
# Hoặc có thể load lại từ file:
# best_model = tf.keras.models.load_model(MODEL_SAVE_PATH)
# val_loss, val_accuracy = best_model.evaluate(val_dataset, verbose=0)
val_loss, val_accuracy = model.evaluate(val_dataset, verbose=0) # Đánh giá trên model hiện tại

print(f"[*] Best Model Validation Accuracy: {val_accuracy * 100:.2f}%")
print(f"[*] Best Model Validation Loss: {val_loss:.4f}")
print(f"[*] Model saved to: {MODEL_SAVE_PATH}")

# Vẽ đồ thị training history
try:
    print("[*] Plotting training history...")
    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    # Số epochs thực tế đã chạy (có thể ít hơn EPOCHS do EarlyStopping)
    epochs_range = range(len(acc))

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label='Training Accuracy')
    plt.plot(epochs_range, val_acc, label='Validation Accuracy')
    plt.legend(loc='lower right')
    plt.title('Training and Validation Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')

    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label='Training Loss')
    plt.plot(epochs_range, val_loss, label='Validation Loss')
    plt.legend(loc='upper right')
    plt.title('Training and Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')

    plt.tight_layout()
    plt.savefig('training_history_imgfolder.png') # Lưu đồ thị ra file ảnh
    print("[*] Training history plot saved as training_history_imgfolder.png")
    # plt.show()
except Exception as plot_error:
      print(f"[!] Warning: Could not plot training history. Error: {plot_error}")


print("[*] Bước 0 (Huấn luyện Model từ thư mục ảnh) hoàn tất.")