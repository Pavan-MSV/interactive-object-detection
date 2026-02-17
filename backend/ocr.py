import easyocr
import numpy as np

class OCRProcessor:
    def __init__(self):
        # Initialize EasyOCR reader for English
        # gpu=False for broader compatibility, set True if CUDA available
        self.reader = easyocr.Reader(['en'], gpu=False) 

    MAX_TEXT_LENGTH = 500  # truncate very long text

    def extract_text(self, image_roi):
        # Keep existing method for backward compatibility if needed, or wrap detect
        try:
            result = self.reader.readtext(image_roi)
            text_list = [item[1] for item in result]
            return " ".join(text_list)
        except Exception:
            return ""

    def detect_text_full(self, image):
        """
        Run OCR on the full image and return detections in standard format:
        {'box': [x1, y1, x2, y2], 'confidence': float, 'class': 'Text', 'ocr_text': str}
        """
        output = []
        try:
            results = self.reader.readtext(image)
            for (bbox, text, prob) in results:
                # bbox is list of 4 points [[x,y], [x,y]..]
                # We need [x1, y1, x2, y2]
                pts = np.array(bbox, dtype=np.int32)
                x1 = int(np.min(pts[:, 0]))
                y1 = int(np.min(pts[:, 1]))
                x2 = int(np.max(pts[:, 0]))
                y2 = int(np.max(pts[:, 1]))
                
                output.append({
                    'box': [x1, y1, x2, y2],
                    'confidence': float(prob),
                    'class': 'Text',
                    'ocr_text': text,
                    'description': f"detected text '{text}'"
                })
        except Exception as e:
            print(f"OCR Full Scan Error: {e}")
        
        return output
