import os
import cv2
import face_recognition

dataset_dir = "my_face_dataset"
print(f"🔍 Scanning all photos in '{dataset_dir}'...")

count_cropped = 0
count_deleted = 0

for root, dirs, files in os.walk(dataset_dir):
    for file in files:
        if file.endswith((".jpg", ".png", ".jpeg")):
            filepath = os.path.join(root, file)
            
            # Read image
            image = cv2.imread(filepath)
            if image is None:
                continue
                
            # Convert to RGB for face_recognition
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Find face
            boxes = face_recognition.face_locations(rgb)
            
            if len(boxes) > 0:
                # Get the coordinates of the first face found
                top, right, bottom, left = boxes[0]
                
                # Add a 20% margin so we don't accidentally cut off the chin or hair
                h = bottom - top
                w = right - left
                margin_h = int(h * 0.2)
                margin_w = int(w * 0.2)
                
                new_top = max(0, top - margin_h)
                new_bottom = min(image.shape[0], bottom + margin_h)
                new_left = max(0, left - margin_w)
                new_right = min(image.shape[1], right + margin_w)
                
                # Crop the image to just the face
                cropped = image[new_top:new_bottom, new_left:new_right]
                
                # Resize to standard size (224x224) to help the AI learn faster
                cropped = cv2.resize(cropped, (224, 224))
                
                # Overwrite the old full-frame image with the new cropped face
                cv2.imwrite(filepath, cropped)
                count_cropped += 1
            else:
                # If no face was found (maybe you blinked or looked away), delete it 
                # so it doesn't confuse the AI
                os.remove(filepath)
                count_deleted += 1

print()
print("==========================================")
print(f"✅ Successfully cropped {count_cropped} faces!")
print(f"🗑️ Deleted {count_deleted} bad photos with no visible face.")
print("==========================================")
print("You can now run train_face_model.py again!")
