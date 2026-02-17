import re

class ReceiptParser:
    def __init__(self):
        pass

    def parse(self, text_detections):
        """
        Parses OCR text detections to extract Shop Name, Items, and Total.
        Expects text_detections to be a list of dicts with 'ocr_text' and 'box'.
        """
        if not text_detections:
            return None

        # Sort by Y coordinate (top to bottom), then X (left to right)
        # box is [x1, y1, x2, y2]
        sorted_dets = sorted(text_detections, key=lambda d: (d['box'][1], d['box'][0]))
        
        lines = self._group_into_lines(sorted_dets)
        
        shop_name = self._extract_shop_name(lines)
        total = self._extract_total(lines)
        items = self._extract_items(lines)

        return {
            "shop_name": shop_name,
            "items": items,
            "total": total
        }

    def _group_into_lines(self, detections, y_threshold=10):
        """Groups detections into lines based on Y-coordinate proximity."""
        lines = []
        current_line = []
        
        for det in detections:
            if not current_line:
                current_line.append(det)
                continue
            
            # Check vertical overlap with the last item in the current line
            last_det = current_line[-1]
            y1_diff = abs(det['box'][1] - last_det['box'][1])
            
            if y1_diff <= y_threshold:
                current_line.append(det)
            else:
                # Sort current line by X
                current_line.sort(key=lambda d: d['box'][0])
                lines.append(current_line)
                current_line = [det]
        
        if current_line:
            current_line.sort(key=lambda d: d['box'][0])
            lines.append(current_line)
            
        return lines

    def _get_line_text(self, line):
        return " ".join([d['ocr_text'] for d in line])

    def _extract_shop_name(self, lines):
        # Heuristic: Shop name is usually the first or second line, often centered or large.
        # For now, just take the first line that looks like a name (not a date/phone).
        for line in lines[:3]:
            text = self._get_line_text(line)
            if len(text) > 3 and not re.search(r'\d{2}/\d{2}', text): # Avoid dates
                return text
        return "Unknown Shop"

    def _extract_total(self, lines):
        # Look for "Total" keyword at the bottom half
        for line in reversed(lines):
            text = self._get_line_text(line).lower()
            if "total" in text:
                # Try to find a number in this line
                match = re.search(r'[\d,]+\.\d{2}', text)
                if match:
                    return match.group(0)
                # Or maybe the number is on the same line but distinct
                # or strictly looking for the largest number at the bottom?
                return self._get_line_text(line) # Return full line if specific number parsing fails
        return None

    def _extract_items(self, lines):
        items = []
        # Heuristic: Lines in the middle that end with a price
        # Skip header (first few lines) and footer (where Total is found)
        # This is tricky without strict structure, but let's try.
        
        start_idx = 0
        end_idx = len(lines)
        
        # refinement: simplistic approach
        for i, line in enumerate(lines):
            text = self._get_line_text(line)
            # Regex for line ending in price like 12.00 or 12.99
            # Allowing for some potential OCR noise or currency symbol
            if re.search(r'\d+\.\d{2}$', text):
                items.append(text)
                
        return items
