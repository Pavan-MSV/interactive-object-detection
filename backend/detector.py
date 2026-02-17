from ultralytics import YOLO
import numpy as np
import cv2
from transformers import ViTImageProcessor, ViTForImageClassification
from PIL import Image
import torch

class ObjectDetector:
    def __init__(self):
        print("Loading models...")
        # 1. Base Model for People (and other objects if desired, filtering for Person)
        self.person_model = YOLO('yolov8x.pt') 
        
        # 2. PPE Model for Helmets
        try:
            self.helmet_model = YOLO('yolov8m_hardhat.pt')
        except Exception as e:
            print(f"Warning: Could not load Helmet model: {e}")
            self.helmet_model = None
        
        print("Loading Vision Transformer (ViT)...")
        try:
            self.processor = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')
            self.vit_model = ViTForImageClassification.from_pretrained('google/vit-base-patch16-224')
        except Exception as e:
            print(f"Warning: Could not load ViT model: {e}")
            self.processor = None
            self.vit_model = None

    def detect_color(self, image_roi):
        """
        Detects the dominant color in the region of interest using K-Means clustering.
        """
        try:
            if image_roi.size == 0: return "Unknown"
            
            # Resize for speed
            data = cv2.resize(image_roi, (50, 50))
            data = data.reshape((-1, 3))
            data = np.float32(data)

            # K-Means
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            k = 1
            _, label, center = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Dominant color (BGR)
            color_bgr = center[0].astype(np.int32)
            
            # Simple color naming logic (reusing existing logic)
            b, g, r = color_bgr
            avg_val = (int(r) + int(g) + int(b)) / 3
            if avg_val > 190: return "White" 
            if avg_val < 50: return "Black"
            
            if r > 150 and g < 100 and b < 100: return "Red"
            if r < 100 and g > 150 and b < 100: return "Green"
            if r < 100 and g < 100 and b > 150: return "Blue"
            if r > 200 and g > 200 and b < 100: return "Yellow"
            if r > 150 and g > 100 and b < 50: return "Orange"
            
            if abs(r - g) < 20 and abs(r - b) < 20 and abs(g - b) < 20: 
                if avg_val > 140: return "White"
                return "Grey"
            
            if r > 150 and g < 50 and b > 150: return "Pink"
            if r < 50 and g > 150 and b > 150: return "Cyan"
            
            # Fallback
            if r >= g and r >= b: return "Reddish"
            if g >= r and g >= b: return "Greenish"
            return "Blueish"
            
        except Exception:
            return "Unknown Color"

    def classify_size(self, box_area, total_area):
        ratio = box_area / total_area
        if ratio < 0.05: return "Small"
        elif ratio < 0.20: return "Medium"
        else: return "Large"

    def refine_class(self, image_roi, original_class):
        """
        Uses ViT to refine generic vehicle classes (Car, Truck, Bus) into specific types
        like Ambulance, Police Car, Fire Engine.
        """
        if not self.vit_model or image_roi.size == 0:
            return original_class
            
        try:
            # Preprocess
            inputs = self.processor(images=image_roi, return_tensors="pt")
            
            # Inference
            with torch.no_grad():
                outputs = self.vit_model(**inputs)
            
            # Get Top Prediction
            logits = outputs.logits
            predicted_class_idx = logits.argmax(-1).item()
            predicted_label = self.vit_model.config.id2label[predicted_class_idx].lower()
            confidence = torch.softmax(logits, dim=-1)[0][predicted_class_idx].item()
            
            # Debug
            # print(f"ViT Prediction for {original_class}: {predicted_label} ({confidence:.2f})")

            # Refinement Logic
            # Only override if confidence is high enough and label is relevant
            if confidence > 0.4: # Adjustable threshold
                if 'ambulance' in predicted_label:
                    return "Ambulance"
                if 'police' in predicted_label:
                    return "Police Car"
                if 'fire engine' in predicted_label or 'fire truck' in predicted_label:
                    return "Fire Engine"
                if 'taxicab' in predicted_label or 'taxi' in predicted_label:
                    return "Taxi"
                if 'school bus' in predicted_label:
                    return "School Bus"
                if 'convertible' in predicted_label:
                    return "Convertible"
                if 'sports car' in predicted_label:
                    return "Sports Car"
                if 'minivan' in predicted_label:
                    return "Minivan"
                if 'pickup' in predicted_label:
                    return "Pickup Truck"

            # Refine 'No Helmet' false positives
            if original_class == 'No Helmet':
                 # Strategy 1: Color Heuristic
                 # Construction helmets are often White, Yellow, Blue, Red, Orange.
                 # Human heads/hair are usually Black, Brown, Grey, Blonde (Yellowish?).
                 # If we detect a strong non-hair color, assume it's a helmet.
                 safety_colors = ['Blue', 'Red', 'Yellow', 'Orange', 'Green', 'Cyan', 'Pink', 'Blueish', 'Reddish', 'Greenish']
                 if color in safety_colors:
                     # Strong indicator of a helmet
                     return "Helmet"
                 
                 # Strategy 2: ViT Confirmation (for White/Grey/Black helmets)
                 if confidence > 0.3:
                     # Check for helmet/hat related terms in ViT
                     helmet_terms = ['helmet', 'crash_helmet', 'hard_hat', 'hat', 'cap', 'head_covering']
                     if any(term in predicted_label for term in helmet_terms):
                         return "Helmet"

        except Exception as e:
            print(f"ViT Refinement Error: {e}")
            
        return original_class

    def detect(self, image, conf=0.45):
        output = []
        total_area = image.shape[0] * image.shape[1]

        # --- RUN 1: Person Detection (YOLOv8x) ---
        # We allow all classes
        results_person = self.person_model(image, conf=conf, iou=0.5)
        
        # --- RUN 2: Helmet Detection (Specialized) ---
        if self.helmet_model:
            results_helmet = self.helmet_model(image, conf=conf, iou=0.5)
        else:
            results_helmet = []

        # Helper to process results
        def process_results(results, model_names, is_ppe=False):
            detections = []
            if not results: return []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    conf_score = box.conf[0].item()
                    cls = int(box.cls[0].item())
                    class_name = model_names[cls]
                    
                    if is_ppe:
                        if class_name == 'Hardhat':
                            class_name = 'Helmet'
                        elif class_name == 'NO-Hardhat':
                            class_name = 'No Helmet'

                    roi = image[max(0, y1):min(image.shape[0], y2), max(0, x1):min(image.shape[1], x2)]
                    color = self.detect_color(roi)
                    size_label = self.classify_size((x2-x1)*(y2-y1), total_area)
                    
                    refined_name = class_name
                    # Attempt Refinement for Vehicles
                    if not is_ppe and class_name.lower() in ['car', 'truck', 'bus', 'train']:
                        refined_name = self.refine_class(roi, class_name)
                    
                    # Attempt Refinement for No Helmet
                    if is_ppe and class_name == 'No Helmet':
                        # Pass 'refined_name' which is currently 'No Helmet'
                        # refine_class expects (roi, original_class)
                        refined_name = self.refine_class(roi, class_name)

                    detections.append({
                        'box': [x1, y1, x2, y2],
                        'confidence': conf_score,
                        'class': refined_name, # Use refined name as primary class? Or separate? 
                                               # Let's use refined as primary for display simple.
                        'original_class': class_name,
                        'color': color,
                        'size': size_label
                    })
            return detections

        # Process and Merge
        start_dets = process_results(results_person, self.person_model.names)
        
        if self.helmet_model:
            ppe_dets = process_results(results_helmet, self.helmet_model.names, is_ppe=True)
        else:
            ppe_dets = []
        
        # --- FILTERING LOGIC ---
        
        # 0. Helper to compute IoU
        def compute_iou(box1, box2):
            x1 = max(box1[0], box2[0])
            y1 = max(box1[1], box2[1])
            x2 = min(box1[2], box2[2])
            y2 = min(box1[3], box2[3])
            
            inter_area = max(0, x2 - x1) * max(0, y2 - y1)
            box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
            box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
            
            union_area = box1_area + box2_area - inter_area
            if union_area == 0: return 0
            return inter_area / union_area

        # 1. Conflict Resolution: Remove 'No Helmet' if overlapping with 'Helmet'
        helmet_boxes = [d for d in ppe_dets if d['class'] == 'Helmet']
        indices_to_remove = set()
        
        for i, d in enumerate(ppe_dets):
            if d['class'] == 'No Helmet':
                for helmet in helmet_boxes:
                    # If it's the exact same object (from my refinement), IoU will be 1.0
                    # If it's a different box but same area, IoU will be distinct.
                    # We want to remove 'No Helmet' if there is a 'Helmet' nearby.
                    if compute_iou(d['box'], helmet['box']) > 0.3:
                        # Caveat: if the 'Helmet' box IS this box (from refinement),
                        # we shouldn't have 'No Helmet' class anymore because I updated 'class' in place.
                        # Wait, in process_results I append to 'detections'.
                        # If I updated 'refined_name', d['class'] IS 'Helmet'.
                        # So this logic only applies if there is a SEPARATE 'No Helmet' detection.
                        # However, if I refined it, d['class'] is ALREADY Helmet.
                        # So this loop only catches cases where one detection remained 'No Helmet'
                        # while ANOTHER detection (maybe from the model directly) says 'Helmet'.
                        indices_to_remove.add(i)
                        break
        
        filtered_ppe_dets = [d for i, d in enumerate(ppe_dets) if i not in indices_to_remove]

        # 2. Person Association
        valid_ppe_dets = []
        if len(start_dets) > 0: 
            for ppe in filtered_ppe_dets:
                is_valid = False
                px1, py1, px2, py2 = ppe['box']
                ppe_center_x = (px1 + px2) / 2
                ppe_center_y = (py1 + py2) / 2
                
                for person in start_dets:
                    if person['original_class'].lower() == 'person': # Check original class for Person
                        bx1, by1, bx2, by2 = person['box']
                        if (bx1 < ppe_center_x < bx2) and (by1 < ppe_center_y < by2):
                            is_valid = True
                            break # Found the person
                            
                if is_valid:
                    valid_ppe_dets.append(ppe)
        
        output.extend(start_dets)
        output.extend(valid_ppe_dets)
        
        return output
