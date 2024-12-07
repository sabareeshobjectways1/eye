import base64
import cv2
import numpy as np
from flask import Flask, jsonify, redirect, render_template, Response, request, url_for
import os

# Initialize Flask app
app = Flask(__name__)

# Directory to save processed images
os.makedirs(os.path.join('static', 'images'), exist_ok=True)

# Load the pre-trained Haar Cascade for eye detection
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Function to detect eyes
def detect_eye(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    eyes = eye_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return len(eyes) > 0  # Return True if at least one eye is detected

# Function to process the image
def process_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    enhanced_img = cv2.equalizeHist(gray)
    edges = cv2.Canny(enhanced_img, 50, 150)
    kernel = np.ones((3, 3), np.uint8)
    processed_image = cv2.dilate(edges, kernel, iterations=1)
    return processed_image

# Function to calculate pressure
def calculate_pressure(length, density):
    systolic_min = 90
    systolic_max = 140
    diastolic_min = 60
    diastolic_max = 90
    original_min = 50
    original_max = 200

    original_pressure = (0.6 * length * density) / 10
    systolic_pressure = systolic_min + (original_pressure - original_min) * \
                        (systolic_max - systolic_min) / (original_max - original_min)
    diastolic_pressure = diastolic_min + (original_pressure - original_min) * \
                         (diastolic_max - diastolic_min) / (original_max - original_min)

    systolic_pressure = max(min(systolic_pressure, systolic_max), systolic_min)
    diastolic_pressure = max(min(diastolic_pressure, diastolic_max), diastolic_min)

    return {
        "systolic": round(systolic_pressure, 2),
        "diastolic": round(diastolic_pressure, 2)
    }

# Function to provide warnings based on pressure
def get_pressure_warning(pressure):
    if pressure["systolic"] > 120:
        return "High Pressure", "danger"
    elif pressure["systolic"] < 90:
        return "Low Pressure", "warning"
    else:
        return "Normal Pressure", "success"

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/ready', methods=['POST'])
def ready_for_test():
    return redirect(url_for('index'))

@app.route('/Eye')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames():
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        return "Error: Camera could not be opened"
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    camera.release()

@app.route('/capture', methods=['POST'])
def capture_and_process():
    try:
        data = request.get_json()
        img_data = data['image']
        img_data = img_data.split(',')[1]
        img_bytes = base64.b64decode(img_data)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if not detect_eye(image):
            return jsonify({
                'pressure': None,
                'message': "No eye detected in the image.",
                'alert_type': "warning",
                'image_path': None
            })

        processed_image = process_image(image)
        processed_image_path = os.path.join('static', 'images', 'processed_image.jpg')
        cv2.imwrite(processed_image_path, processed_image)

        vessel_length = np.sum(processed_image > 0)
        vessel_density = vessel_length / processed_image.size
        estimated_pressure = calculate_pressure(vessel_length, vessel_density)
        message, alert_type = get_pressure_warning(estimated_pressure)

        return jsonify({
            'pressure': estimated_pressure,
            'message': message,
            'alert_type': alert_type,
            'image_path': 'images/processed_image.jpg'
        })

    except Exception as e:
        return jsonify({
            'pressure': None,
            'message': f"Error processing image: {str(e)}",
            'alert_type': "danger",
            'image_path': None
        })

@app.route('/stop')
def stop_camera():
    cv2.destroyAllWindows()
    return "Camera stopped"

if __name__ == '__main__':
    app.run(debug=True)
