import ast
import cv2
import numpy as np
import pandas as pd


# Load the detection results
csv_file = "C:\\Users\\PC-ACER\\Desktop\\anpr\\results.csv"   # Use the correct output file from main.py
results = pd.read_csv(csv_file)

# Load the video
video_path = './sample.mp4'
cap = cv2.VideoCapture(video_path)

# Output video settings
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out = cv2.VideoWriter('./out_visualized.mp4', fourcc, fps, (width, height))


# 🛠️ Helper function to fix malformed bounding boxes
def fix_bbox_format(bbox_str):
    """Ensure bounding box has correct comma formatting."""
    try:
        bbox_str = bbox_str.replace("[", "").replace("]", "").split()

        # Ensure it contains 4 values
        if len(bbox_str) == 4:
            bbox_str = f"[{bbox_str[0]}, {bbox_str[1]}, {bbox_str[2]}, {bbox_str[3]}]"
        else:
            print(f"⚠️ Malformed bbox: {bbox_str}")
            return "[0, 0, 0, 0]"  # Return a default bbox for safety

        return bbox_str
    except Exception as e:
        print(f"Error fixing bbox: {e}")
        return "[0, 0, 0, 0]"  # Return a safe bbox


# Helper function: Draw corner borders
def draw_border(img, top_left, bottom_right, color=(0, 255, 0), thickness=10, line_length=100):
    """Draws corner borders around the bounding box."""
    x1, y1 = top_left
    x2, y2 = bottom_right

    # Top-left
    cv2.line(img, (x1, y1), (x1 + line_length, y1), color, thickness)
    cv2.line(img, (x1, y1), (x1, y1 + line_length), color, thickness)

    # Top-right
    cv2.line(img, (x2, y1), (x2 - line_length, y1), color, thickness)
    cv2.line(img, (x2, y1), (x2, y1 + line_length), color, thickness)

    # Bottom-left
    cv2.line(img, (x1, y2), (x1 + line_length, y2), color, thickness)
    cv2.line(img, (x1, y2), (x1, y2 - line_length), color, thickness)

    # Bottom-right
    cv2.line(img, (x2, y2), (x2 - line_length, y2), color, thickness)
    cv2.line(img, (x2, y2), (x2, y2 - line_length), color, thickness)

    return img


# Prepare license plate dictionary for overlay
license_plate = {}

# Extract the best license plate for each car
for car_id in np.unique(results['car_id']):
    car_df = results[results['car_id'] == car_id]

    # Get the license plate with the highest score
    max_score_idx = car_df['license_number_score'].idxmax()
    best_plate = car_df.loc[max_score_idx]

    frame_nmr = int(best_plate['frame_nmr'])
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_nmr)

    ret, frame = cap.read()

    if not ret:
        continue

    # ✅ Use bbox fix function to ensure proper formatting
    x1, y1, x2, y2 = ast.literal_eval(fix_bbox_format(best_plate['license_plate_bbox']))

    license_crop = frame[int(y1):int(y2), int(x1):int(x2)]

    if license_crop.size > 0:
        license_crop = cv2.resize(license_crop, (200, 50))

        license_plate[car_id] = {
            'license_crop': license_crop,
            'license_plate_number': best_plate['license_number']
        }

# Reset video to start
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

# Visualization loop
frame_nmr = -1
ret = True

while ret:
    ret, frame = cap.read()
    frame_nmr += 1

    if not ret:
        break

    # Get detections for the current frame
    df_ = results[results['frame_nmr'] == frame_nmr]

    for _, row in df_.iterrows():
        # ✅ Use bbox fix function here to prevent parsing issues
        car_bbox = ast.literal_eval(fix_bbox_format(row['car_bbox']))
        car_x1, car_y1, car_x2, car_y2 = map(int, car_bbox)

        draw_border(frame, (car_x1, car_y1), (car_x2, car_y2), color=(0, 255, 0), thickness=12)

        plate_bbox = ast.literal_eval(fix_bbox_format(row['license_plate_bbox']))
        x1, y1, x2, y2 = map(int, plate_bbox)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 5)

        car_id = row['car_id']

        if car_id in license_plate:
            plate_crop = license_plate[car_id]['license_crop']
            plate_number = license_plate[car_id]['license_plate_number']

            H, W, _ = plate_crop.shape

            # Display the license plate crop above the car
            x_offset = max(0, int((car_x2 + car_x1 - W) / 2))
            y_offset = max(0, car_y1 - H - 20)

            try:
                # Overlay the license plate image above the car
                frame[y_offset:y_offset + H, x_offset:x_offset + W] = plate_crop

                # Draw the license plate number
                cv2.putText(frame,
                            plate_number,
                            (x_offset, y_offset - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.5,
                            (0, 255, 255),
                            4)

            except Exception as e:
                print(f"Warning: Skipped overlay due to {e}")

    # Write the frame with visualizations
    out.write(frame)

    # Display preview
    display_frame = cv2.resize(frame, (1280, 720))
    cv2.imshow("ANPR Visualization", display_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
out.release()
cap.release()
cv2.destroyAllWindows()

print("✅ Visualization saved to './out_visualized.mp4'")
