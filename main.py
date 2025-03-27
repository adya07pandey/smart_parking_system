import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from ultralytics import YOLO
import cv2
from deep_sort_realtime.deepsort_tracker import DeepSort
from util import get_car, read_license_plate, write_csv

# Initialize models
object_model = YOLO("C:\\Users\\PC-ACER\\Desktop\\anpr\\yolov8n.pt")
license_plate_detector = YOLO("C:\\Users\\PC-ACER\\Desktop\\anpr\\license_plate_detector.pt")

deepsort_tracker = DeepSort(max_age=30, n_init=3, nms_max_overlap=1.0)

# Video capture
cap = cv2.VideoCapture("C:\\Users\\PC-ACER\\Desktop\\anpr\\sample.mp4")

csv_file = "./results.csv"
results = {}

# Frame processing
frame_no = -1
vehicles = [2, 3, 5, 7]


while cap.isOpened():
    ret, frame = cap.read()
    frame_no += 1
    if not ret:
        break

    results[frame_no] = {}

    # ✅ Vehicle detection
    vehicle_detections = object_model(frame)[0]

    detected = []
    for box in vehicle_detections.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        score = box.conf[0].item()
        class_id = int(box.cls[0])

        if class_id in vehicles:
            detected.append(([x1, y1, x2 - x1, y2 - y1], score, class_id))

    # ✅ DeepSORT tracking
    if frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
        track_ids = deepsort_tracker.update_tracks(detected, frame=frame)

    # ✅ License plate detection
    license_plates = license_plate_detector(frame)[0]

    for box in license_plates.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        score = box.conf[0].item()
        class_id = int(box.cls[0])

        # 👉 Pass the full detection tuple to get_car()
        xcar1, ycar1, xcar2, ycar2, car_id = get_car((x1, y1, x2, y2, score, class_id), track_ids)

        if car_id != -1:
            # Extract and process the license plate
            license_plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]

            # Convert to grayscale
            license_plate_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
            _, license_plate_thresh = cv2.threshold(license_plate_gray, 64, 255, cv2.THRESH_BINARY_INV)

            # OCR the license plate
            license_plate_text, license_plate_text_score = read_license_plate(license_plate_thresh)

            if license_plate_text is not None:
                results[frame_no][car_id] = {
                    'car': {'bbox': [xcar1, ycar1, xcar2, ycar2]},
                    'license_plate': {
                        'bbox': [x1, y1, x2, y2],
                        'text': license_plate_text,
                        'bbox_score': score,
                        'text_score': license_plate_text_score
                    }
                }

# ✅ Save results to CSV
write_csv(results, csv_file)

# Cleanup
cap.release()
cv2.destroyAllWindows()

print(f"✅ Results saved to {csv_file}")
