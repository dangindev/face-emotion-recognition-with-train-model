# app/services.py
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import tensorflow as tf
import base64
import io
from PIL import Image
import os
import time
import traceback

# --- Import DeepFace ---
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
    print("\n   ✅ DeepFace library imported successfully.")
except ImportError:
    print("\n   ❌ ERROR: DeepFace library not found. Option 'deepface' will not work.")
    print("     Please install it: pip install deepface")
    DeepFace = None # Set to None so checks later will fail gracefully
    DEEPFACE_AVAILABLE = False

print("\n==================================================")
print(" Initializing AI Services - VERSION: CUSTOM + DEEPFACE ")
print("==================================================")

# --- Configuration ---
# Face Detection (Used by both)
CASCADE_FILENAME = 'haarcascade_frontalface_default.xml'

# Custom Model Configuration
CUSTOM_MODEL_ID = 'custom' # Key used in frontend/backend communication
CUSTOM_MODEL_FILENAME = 'emotion_detection_model.h5' # Your trained model file
CUSTOM_MODEL_INPUT_SIZE = (48, 48)
CUSTOM_MODEL_EXPECTS_GRAYSCALE = True
CUSTOM_MODEL_LABELS = { # MAKE SURE THIS ORDER MATCHES YOUR TRAINING LOG OUTPUT!
    0: 'angry', 1: 'disgust', 2: 'fear', 3: 'happy',
    4: 'neutral', 5: 'sad', 6: 'surprise'
}
CUSTOM_MODEL_NORMALIZATION = 'divide_by_255' # How pixels were normalized for training

# DeepFace Model Configuration (Mainly for reference, DeepFace handles internal details)
DEEPFACE_MODEL_ID = 'deepface' # Key used in frontend/backend communication

# --- Global Variables ---
custom_emotion_model = None # Variable to hold the loaded custom model
face_cascade = None         # Variable to hold the loaded cascade
cascade_loaded = False
custom_model_loaded = False

# --- Load Face Detection Cascade ---
print(f"[*] Attempting to load Face Cascade: '{CASCADE_FILENAME}'")
cascade_path_cv2 = os.path.join(cv2.data.haarcascades, CASCADE_FILENAME)
print(f"    Trying OpenCV data path: {cascade_path_cv2}")
if os.path.exists(cascade_path_cv2):
    try:
        face_cascade = cv2.CascadeClassifier(cascade_path_cv2)
        if face_cascade.empty():
            print(f"    ⚠️ WARNING: Cascade file loaded but is empty.")
            face_cascade = None
        else:
            print(f"    ✅ SUCCESS: Face cascade loaded from OpenCV data.")
            cascade_loaded = True
    except Exception as e:
         print(f"   ❌ ERROR loading face cascade: {e}")
else:
    # Try loading locally (optional fallback)
    cascade_path_local = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', CASCADE_FILENAME))
    print(f"    Cascade not in OpenCV data. Trying local path: {cascade_path_local}")
    if os.path.exists(cascade_path_local):
         try:
             face_cascade = cv2.CascadeClassifier(cascade_path_local)
             if face_cascade.empty(): face_cascade = None
             else: print(f"    ✅ SUCCESS: Local Face cascade loaded."); cascade_loaded = True
         except Exception as e: print(f"   ❌ ERROR loading local face cascade: {e}")
    else:
         print(f"   ❌ ERROR: Cascade file not found in OpenCV data or locally.")

# --- Load Custom Emotion Model ---
if cascade_loaded: # Only load if face detection is available
    print(f"\n[*] Attempting to load Custom CNN model: '{CUSTOM_MODEL_FILENAME}'")
    model_path_relative = os.path.join(os.path.dirname(__file__), '..', CUSTOM_MODEL_FILENAME)
    model_path_absolute = os.path.abspath(model_path_relative)
    print(f"    Full path: {model_path_absolute}")

    if os.path.exists(model_path_absolute):
        try:
            # Load the custom model (use compile=False if metrics cause issues on load)
            custom_emotion_model = tf.keras.models.load_model(model_path_absolute, compile=False)
            print(f"    ✅ SUCCESS: Custom model ('{CUSTOM_MODEL_FILENAME}') loaded.")
            custom_model_loaded = True
        except Exception as e:
            print(f"    ❌ ERROR loading custom model: {e}")
            # traceback.print_exc()
    else:
        print(f"    ❌ ERROR: Custom model file NOT FOUND.")
else:
    print("\n[!] Skipping custom emotion model loading because face cascade failed.")


print("\n--- Service Status ---")
print(f" Face Cascade Loaded: {cascade_loaded}")
print(f" Custom Model Loaded: {custom_model_loaded}")
print(f" DeepFace Library Available: {DEEPFACE_AVAILABLE}")
print("==================================================")
print(" Finished initializing AI Services")
print("==================================================")

# --- Helper Function: Decode Base64 Image ---
def decode_image(base64_string):
    """Decodes base64 string to an OpenCV image (BGR format)."""
    try:
        if isinstance(base64_string, str) and ',' in base64_string:
            base64_string = base64_string.split(',', 1)[1]
        img_bytes = base64.b64decode(base64_string)
        img_pil = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(img_pil)
        # Convert various formats to BGR for consistency
        if len(img_array.shape) == 2: img_cv2 = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
        elif len(img_array.shape) == 3 and img_array.shape[2] == 3: img_cv2 = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        elif len(img_array.shape) == 3 and img_array.shape[2] == 4: img_cv2 = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        else: print(f"   [decode_image Error] Unexpected shape: {img_array.shape}"); return None
        return img_cv2
    except ValueError as ve: print(f"   [decode_image Error] Invalid base64: {ve}"); return None
    except Exception as e: print(f"   [decode_image Error] General error: {e}"); return None

# --- Helper Function: Preprocess for Custom Model ---
def preprocess_for_custom_model(face_roi):
    """Preprocesses the detected face ROI for the CUSTOM CNN model."""
    try:
        target_size = CUSTOM_MODEL_INPUT_SIZE
        expect_grayscale = CUSTOM_MODEL_EXPECTS_GRAYSCALE
        normalization_type = CUSTOM_MODEL_NORMALIZATION

        # 1. Convert Color
        if expect_grayscale:
            if len(face_roi.shape) >= 2: processed_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            else: raise ValueError("Invalid ROI shape for grayscale")
        else:
            processed_roi = face_roi # Assume BGR

        # 2. Resize
        if processed_roi.shape[0] > target_size[1] or processed_roi.shape[1] > target_size[0]: interpolation = cv2.INTER_AREA
        else: interpolation = cv2.INTER_LINEAR
        processed_roi = cv2.resize(processed_roi, target_size, interpolation=interpolation)

        # 3. Normalize
        if normalization_type == 'divide_by_255':
            processed_roi = processed_roi / 255.0
        # Add other normalization logic if needed

        # 4. Reshape
        if expect_grayscale: roi_input = np.expand_dims(np.expand_dims(processed_roi, axis=-1), axis=0)
        else: roi_input = np.expand_dims(processed_roi, axis=0)

        return roi_input.astype('float32')

    except Exception as e:
        print(f"   [preprocess_custom Error] Failed: {e}")
        traceback.print_exc()
        return None

# --- Main Processing Function ---
def detect_emotion_and_attention(image_cv2, requested_model_id='custom'):
    """
    Detects face, predicts emotion using the requested method (custom or deepface),
    and estimates attention.
    """
    start_func_time = time.time()
    dominant_emotion = "N/A"
    is_attentive = False

    # Check fundamental requirements first
    if image_cv2 is None: return "Error: Invalid Input", False
    if not cascade_loaded: return "Error: Cascade Missing", False # Cannot proceed without cascade

    # --- Face Detection ---
    faces = []
    try:
        gray_img = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
        img_h, img_w = image_cv2.shape[:2]
        faces = face_cascade.detectMultiScale(gray_img, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40), flags=cv2.CASCADE_SCALE_IMAGE)
    except Exception as e:
        print(f"   [detect] Error during face detection: {e}")
        return "Error: Detection Failed", False

    # --- Process the Largest Face (if any) ---
    if len(faces) > 0:
        faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
        (x, y, w, h) = faces[0]
        face_roi = image_cv2[y:y+h, x:x+w] # Extract BGR ROI

        # --- Emotion Prediction based on request ---
        emotion_predicted = False # Flag to check if prediction was attempted

        if requested_model_id == DEEPFACE_MODEL_ID:
            if DEEPFACE_AVAILABLE:
                # print("   [detect] Using DeepFace for prediction...")
                try:
                    # DeepFace prefers BGR images (like OpenCV outputs)
                    # Setting detector_backend='skip' might be slightly faster if Haar cascade already did well
                    results = DeepFace.analyze(img_path=face_roi,
                                              actions=['emotion'],
                                              enforce_detection=False, # We already detected the face
                                              detector_backend='opencv', # or 'skip' ? Test performance
                                              silent=True) # Suppress internal DeepFace logs

                    if results and isinstance(results, list) and len(results) > 0:
                        # DeepFace often returns a list containing one dictionary
                        dominant_emotion = results[0]['dominant_emotion'].capitalize()
                        emotion_predicted = True
                        # print(f"      DeepFace Result: '{dominant_emotion}'")
                    else:
                        print("      [detect] DeepFace analyze returned empty or unexpected result.")
                        dominant_emotion = "N/A (DeepFace Eval)" # Indicate evaluation issue

                except ValueError as ve: # Often means face not detected *by DeepFace* inside ROI
                    print(f"      [detect] DeepFace ValueError (likely no face in ROI): {ve}")
                    dominant_emotion = "No face detected (DF)" # Distinguish from OpenCV 'no face'
                except Exception as df_err:
                    print(f"      [detect] DeepFace Analyze Error: {df_err}")
                    dominant_emotion = "Error: DeepFace Failed"
                    # traceback.print_exc() # Enable for deep debug
            else:
                print("   [detect] DeepFace selected but library not available.")
                dominant_emotion = "N/A (DeepFace Unavailable)"

        elif requested_model_id == CUSTOM_MODEL_ID:
            # print("   [detect] Using Custom .h5 model for prediction...")
            if custom_model_loaded:
                try:
                    # Preprocess specifically for the custom model
                    cnn_input = preprocess_for_custom_model(face_roi)

                    if cnn_input is not None:
                        # Predict using the custom loaded model
                        emotion_prediction_vector = custom_emotion_model.predict(cnn_input, verbose=0)
                        emotion_index = np.argmax(emotion_prediction_vector[0])
                        dominant_emotion = CUSTOM_MODEL_LABELS.get(emotion_index, f"Unknown Index:{emotion_index}")
                        dominant_emotion = dominant_emotion.capitalize() # Capitalize first letter
                        emotion_predicted = True
                        # print(f"      Custom Model Result: '{dominant_emotion}'")
                    else:
                        dominant_emotion = "Error: Custom Preprocessing Failed"
                except Exception as pred_err:
                    print(f"      [detect] Custom Model Prediction Error: {pred_err}")
                    dominant_emotion = "Error: Custom Prediction Failed"
                    # traceback.print_exc()
            else:
                dominant_emotion = "N/A (Custom Model not loaded)"
        else:
            # Handle unknown model ID if necessary
            print(f"   [detect] Unknown requested model ID: '{requested_model_id}'")
            dominant_emotion = f"Error: Unknown model"

        # If no emotion prediction happened or failed, reflect that (unless face wasn't detected initially)
        if not emotion_predicted and dominant_emotion == "N/A":
             dominant_emotion = "N/A (Prediction Skipped/Failed)"


        # --- Attention Check (Independent of emotion model used) ---
        try:
            face_center_x = x + w // 2
            attention_zone_start = 0.15 * img_w
            attention_zone_end = 0.85 * img_w
            is_attentive = attention_zone_start < face_center_x < attention_zone_end
        except Exception as attn_err:
            print(f"   [detect] Error during attention check: {attn_err}")
            is_attentive = False

    else: # No face detected by OpenCV Cascade
        dominant_emotion = "No face detected"
        is_attentive = False

    # --- Return results ---
    # print(f"   [detect] -> ('{dominant_emotion}', {is_attentive})") # Final result debug
    return dominant_emotion, is_attentive