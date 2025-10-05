import cv2
import os
import numpy as np
from datetime import datetime

PHOTO_DIR = "./photos"
DATASET_DIR = "./dataset"

def capture_from_camera(save_path=None):
    if save_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"./photos/real_img_{timestamp}.jpg"
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open camera")
            return None
            
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(save_path, frame)
            print(f"✅ Captured and saved to {save_path}")
            cap.release()
            return save_path
        else:
            print("❌ Failed to capture image")
            cap.release()
            return None
    except Exception as e:
        print(f"❌ Camera error: {e}")
        return None

def compare_images(img1_path, img2_path):
    try:
        img1 = cv2.imread(img1_path, 0)
        img2 = cv2.imread(img2_path, 0)
        
        if img1 is None or img2 is None:
            return 0

        orb = cv2.ORB_create()
        kp1, des1 = orb.detectAndCompute(img1, None)
        kp2, des2 = orb.detectAndCompute(img2, None)

        if des1 is None or des2 is None:
            return 0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        score = len(matches)
        return score
    except Exception as e:
        print(f"❌ Error comparing images: {e}")
        return 0

def find_best_match(real_img_path):
    best_score = 0
    best_match = None
    total_comparisons = 0

    print("🔍 Searching for best match...")
    
    for root, dirs, files in os.walk(DATASET_DIR):
        for file in files:
            if file.endswith(".png"):
                dataset_img = os.path.join(root, file)
                score = compare_images(real_img_path, dataset_img)
                total_comparisons += 1
                
                if score > best_score:
                    best_score = score
                    best_match = dataset_img
                    print(f"🎯 New best match: {best_match} (score: {best_score})")

    print(f"📊 Compared with {total_comparisons} images")
    return best_match, best_score

if __name__ == "__main__":
    print("📷 Starting camera capture and matching...")
    
    # Check if dataset exists
    if not os.path.exists(DATASET_DIR):
        print(f"❌ Dataset directory not found: {DATASET_DIR}")
        print("💡 Please run generate_images.py first to create the dataset")
        exit(1)
    
    # Capture image from camera
    real_img_path = capture_from_camera()
    
    if real_img_path:
        # Find best match
        best_match, best_score = find_best_match(real_img_path)
        
        if best_match:
            print(f"🏆 Best Match: {best_match}")
            print(f"📊 Match Score: {best_score}")
            
            # Extract model name from path
            model_name = os.path.basename(os.path.dirname(best_match))
            print(f"🎯 Identified Model: {model_name}")
        else:
            print("❌ No matches found")
    else:
        print("❌ Failed to capture image from camera")