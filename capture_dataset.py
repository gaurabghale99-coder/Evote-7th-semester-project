# capture_dataset.py
import cv2
import os
import sys

print("=== Face Dataset Capture Tool ===")
print()

voter_id = input("Enter voter ID (e.g. V001_Gaurab): ").strip()
if not voter_id:
    print("Error: You must enter a voter ID!")
    sys.exit(1)

save_dir = f"my_face_dataset/{voter_id}"
os.makedirs(save_dir, exist_ok=True)
print(f"Saving photos to: {save_dir}/")

print("Opening camera...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Cannot open camera!")
    print("Make sure no other app (like uvicorn/browser) is using the camera.")
    sys.exit(1)

print("Camera opened successfully!")
count = 0

print()
print("==========================================")
print("  SPACE = Capture photo  |  Q = Quit")
print("==========================================")
print()

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("ERROR: Cannot read frame from camera!")
        break

    # Show count on the frame itself
    display = frame.copy()
    cv2.putText(display, f"Photos: {count}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(display, "SPACE=Capture | Q=Quit", (10, 65), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow("Capture Dataset - Press SPACE", display)

    key = cv2.waitKey(1) & 0xFF
    if key == ord(' '):  # Space to capture
        path = f"{save_dir}/{count:03d}.jpg"
        cv2.imwrite(path, frame)
        count += 1
        print(f"  ✅ Saved {path} ({count} total)")
    elif key == ord('q'):
        print(f"\nDone! Captured {count} photos for {voter_id}")
        break

cap.release()
cv2.destroyAllWindows()
