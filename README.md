# Emotion Focus App

![Emotion Focus App](training_history_imgfolder.png)

## Overview
The Emotion Focus App is a machine learning-powered application designed to detect and classify human emotions from facial expressions. It leverages Convolutional Neural Networks (CNNs) and pre-trained models to provide accurate emotion recognition.

## Features
- **Emotion Detection**: Classifies emotions into categories such as Angry, Disgust, Fear, Happy, Neutral, Sad, and Surprise.
- **User Authentication**: Secure login and registration system.
- **Interactive UI**: User-friendly interface built with HTML, CSS, and JavaScript.
- **Visualization**: Displays training history and performance metrics.

## Project Structure
```
config.py
emotion_cnn_model.h5
emotion_detection_model.h5
facenet_keras.h5
README.md
run.py
train_model.py
training_history_imgfolder.png
__pycache__/
app/
    __init__.py
    forms.py
    models.py
    routes.py
    services.py
    static/
        css/
            style.css
        js/
            main.js
    templates/
        base.html
        history.html
        index.html
        login.html
        register.html
dataset/
    test/
        angry/
        disgust/
        fear/
        happy/
        neutral/
        sad/
        surprise/
    train/
        angry/
        disgust/
        fear/
        happy/
        neutral/
        sad/
        surprise/
instance/
    app_data.db
```

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/emotion_focus_app.git
   ```
2. Navigate to the project directory:
   ```bash
   cd emotion_focus_app
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run the application:
   ```bash
   python run.py
   ```
2. Open your browser and navigate to `http://127.0.0.1:5000`.
3. Register or log in to start using the app.

## Dataset
The dataset is organized into `train` and `test` directories, each containing subdirectories for different emotion categories:
- Angry
- Disgust
- Fear
- Happy
- Neutral
- Sad
- Surprise

## Model Training and Results
To train the model, use the `train_model.py` script. The training history and performance metrics are visualized below:

### Training and Validation Accuracy
![Training and Validation Accuracy](app/static/images/history.png)

### Training and Validation Loss
The model shows consistent improvement in accuracy and reduction in loss over epochs, as seen in the graphs above.

If you prefer to use the pre-trained model directly, the application includes a pre-trained model (`emotion_cnn_model.h5`) for immediate use. This ensures you can run the application without retraining the model.

## Quick Start Guide
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/emotion_focus_app.git
   ```
2. Navigate to the project directory:
   ```bash
   cd emotion_focus_app
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python run.py
   ```
5. Open your browser and navigate to `http://127.0.0.1:5000`.
6. Register or log in to start using the app with the pre-trained model.

## Screenshots
### Home Page
![Home Page](app/static/images/home_page.png)

### Emotion Detection
![Emotion Detection](app/static/images/emotion_detection.png)

### History Analysis
![History Analysis](app/static/images/history.png)

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contact
For any inquiries, please contact [haidang29productions@gmail.com](haidang29productions@gmail.com).