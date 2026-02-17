from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import shutil
import os
import cv2
import numpy as np
from detector import ObjectDetector
from ocr import OCRProcessor
from receipt_parser import ReceiptParser

app = FastAPI()

# CORS configuration
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
# Initialize engines
detector = ObjectDetector()
ocr_processor = OCRProcessor()
receipt_parser = ReceiptParser()
# detector = None
# ocr_processor = None

@app.get("/api-health")
def read_root():
    return {"message": "Object Detection & OCR API is running"}



@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        temp_file = f"temp_{file.filename}"
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Read image
        image = cv2.imread(temp_file)
        if image is None:
            os.remove(temp_file)
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Object Detection (YOLO)
        detections = detector.detect(image)
        
        # Text Detection (EasyOCR Full Scan)
        text_detections = ocr_processor.detect_text_full(image)

        # --- BILL / RECEIPT DETECTION LOGIC ---
        bill_data = None
        # Heuristic: If there are many text detections (e.g. > 10) and few/no natural objects
        # or if specific keywords like "Total", "Subtotal" are found.
        
        # For a robust check, let's look for "Total" or high text count
        has_total = any("total" in d['ocr_text'].lower() for d in text_detections)
        if len(text_detections) > 10 or has_total:
            parsed_bill = receipt_parser.parse(text_detections)
            if parsed_bill and (parsed_bill['total'] or len(parsed_bill['items']) > 0):
                bill_data = parsed_bill

        # Merge results
        # We want to associate text with objects if they overlap significantly, 
        # otherwise treat text as a separate object.
        
        final_results = []
        
        # helper to check intersection
        def get_iou(boxA, boxB):
            xA = max(boxA[0], boxB[0])
            yA = max(boxA[1], boxB[1])
            xB = min(boxA[2], boxB[2])
            yB = min(boxA[3], boxB[3])
            interArea = max(0, xB - xA) * max(0, yB - yA)
            boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
            if boxAArea == 0: return 0
            return interArea / boxAArea # intersection over object area

        # 1. Add YOLO detections
        for det in detections:
            # Check if any text box overlaps this object
            associated_text = []
            for text_det in text_detections:
                if get_iou(det['box'], text_det['box']) > 0.3: # 30% overlap
                    associated_text.append(text_det['ocr_text'])
            
            ocr_text_combined = " ".join(associated_text)
            det['ocr_text'] = ocr_text_combined
            
            # STRICTLY use the detected class name.
            main_obj = det['class'] # This might be "Ambulance" now thanks to ViT
            
            # --- VEHICLE NUMBER PLATE LOGIC ---
            # If it's a vehicle, let's try to find a number plate specifically
            # Even if we didn't find one in the full scan, we might find one by cropping?
            # For now, let's check if we ALREADY found text that looks like a plate patterns,
            # OR we can execute a specific crop OCR here if we want to be very thorough.
            # To be efficient, let's rely on the full text scan first, but if we need more accuracy,
            # we should crop.
            # User requirement: "give at the side detected number plate is xyz626"
            
            number_plate_text = ""
            if main_obj.lower() in ['car', 'truck', 'bus', 'motorcycle', 'vehicle', 'ambulance', 'police car', 'taxi', 'van']:
                # Strategy: Look at associated text. If it matches a plate pattern, use it.
                # Regex for general plates: alphanumeric, 5-10 chars?
                # or just take the most prominent text associated with the bumper area?
                # Simple approach: If associated text is short and alphanumeric, assume it's a plate.
                
                # Let's try to refine by cropping the bottom half of the vehicle?
                # Actually, main OCR scan is usually good enough if resolution is high.
                # Let's look for text that was associated.
                if associated_text:
                    # Filter for plate-like text
                    for t in associated_text:
                        if len(t) > 4 and sum(c.isdigit() for c in t) > 0 and sum(c.isalpha() for c in t) > 0:
                             number_plate_text = t
                             break
                    if not number_plate_text and len(associated_text) > 0:
                        # Fallback: just use the text
                        number_plate_text = associated_text[0]
                
                if number_plate_text:
                    det['number_plate'] = number_plate_text

            
            # --- HELMET ASSOCIATION LOGIC ---
            helmet_status = ""
            if main_obj.lower() == 'person':
                # Check for overlapping 'Hardhat' or 'NO-Hardhat'
                for other_det in detections:
                    if other_det == det: continue
                    other_obj = other_det['class']
                    # Check intersection
                    oh_x1, oh_y1, oh_x2, oh_y2 = other_det['box']
                    oh_center_x = (oh_x1 + oh_x2) / 2
                    oh_center_y = (oh_y1 + oh_y2) / 2
                    
                    p_x1, p_y1, p_x2, p_y2 = det['box']
                    
                    if (p_x1 < oh_center_x < p_x2) and (p_y1 < oh_center_y < p_y2):
                         if other_obj == 'Helmet':
                             helmet_status = "wearing a helmet"
                         elif other_obj == 'No Helmet':
                             helmet_status = "not wearing a helmet"
            
            if main_obj.lower() == 'helmet':
                base_desc = f"detected a {main_obj}"
            else:
                base_desc = f"detected a {det['color'].lower()} {main_obj}"
            
            if helmet_status:
                base_desc += f" {helmet_status}"
            
            if det.get('number_plate'):
                base_desc += f", Number Plate: {det['number_plate']}"

            if not det.get('number_plate') and ocr_text_combined:
                det['description'] = f"{base_desc} containing text '{ocr_text_combined}'"
            else:
                det['description'] = base_desc
            
            final_results.append(det)

        # 2. Add Standalone Text
        # We might want to HIDE text if it was used for a receipt/bill to avoid clutter?
        # If bill_data is found, maybe suppress individual text nodes in the UI, or keep them?
        # Let's keep them for now, but maybe the UI can filter them.
        
        for text_det in text_detections:
            is_inside_object = False
            
            for det in detections:
                if get_iou(det['box'], text_det['box']) > 0.5:
                    is_inside_object = True
                    break
            
            if not is_inside_object:
                final_results.append(text_det)
        
        results = final_results

        # Cleanup
        os.remove(temp_file)
        
        # IMPROVEMENT: Generate Overall Scene Summary
        summary_items = []
        detected_text = []

        for det in results:
            if det['class'] == 'Text':
                if det.get('ocr_text'):
                    detected_text.append(det['ocr_text'])
                continue
            
            is_auxiliary = det['class'] in ['Helmet', 'No Helmet']
            
            item_desc = det['class']
            
            if det['class'].lower() == 'person':
                if "wearing a helmet" in det.get('description', ''):
                    item_desc = "Person (with Helmet)"
                elif "not wearing a helmet" in det.get('description', ''):
                    item_desc = "Person (No Helmet)"
            
            if det.get('color') and det['color'] != "Unknown Color":
                item_desc = f"{det['color']} {item_desc}"
            
            if not is_auxiliary:
                summary_items.append(item_desc) 

        # Count items
        from collections import Counter
        item_counts = Counter(summary_items)
        
        summary_parts = []
        for item, count in item_counts.items():
            summary_parts.append(f"{count} {item}{'s' if count > 1 else ''}")
        
        if summary_parts:
            summary_text = "This image contains " + ", ".join(summary_parts) + "."
        else:
            summary_text = "No objects were clearly detected."

        if bill_data:
            summary_text += f" It appears to be a Shop Bill from '{bill_data['shop_name']}' with {len(bill_data['items'])} items totaling {bill_data['total'] or 'Unknown'}."
        elif detected_text: # Only show random text if not a bill, to avoid spam
            unique_text = list(set(detected_text))[:3]
            summary_text += f" It also features text: '{', '.join(unique_text)}'."

        return {"results": results, "summary": summary_text, "bill_data": bill_data, "filename": file.filename}

    except Exception as e:
        if os.path.exists(f"temp_{file.filename}"):
             os.remove(f"temp_{file.filename}")
        raise HTTPException(status_code=500, detail=str(e))

from pathlib import Path

# ... (imports)

# Resolve absolute path to frontend
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

if not FRONTEND_DIR.exists():
    print(f"WARNING: Frontend directory not found at {FRONTEND_DIR}")

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
