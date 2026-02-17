---
title: Interactive Object Detection
emoji: 🕵️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# VisionSync - Interactive Object Detection & OCR

**VisionSync** is an advanced AI-powered web application that performs real-time object detection and text recognition (OCR) on images. It features a modern, interactive interface that allows users to explore detected objects, read extracted text, and get intelligent scene summaries.

## 🌟 Features

-   **Advanced Object Detection**: Uses **YOLOv8 Medium** for high-accuracy detection of common objects.
-   **Smart OCR**: Integrated **EasyOCR** engine to read text from signs, documents, and messy backgrounds.
-   **Global Text Search**: Detects text anywhere in the image, even outside of standard objects.
-   **Intelligent Descriptions**: Auto-generates natural language descriptions (e.g., *"detected a coffee cup containing text 'Morning'"*).
-   **Scene Summary**: Provides a smart overview of the entire image content (e.g., *"This image contains A, B, and C..."*).
-   **Interactive UI**:
    -   Drag & Drop Upload
    -   Clickable Bounding Boxes
    -   Real-time Search & Filter
    -   Dark Mode & Glassmorphism Design

## 🛠️ Tech Stack

-   **Backend**: Python, FastAPI
-   **AI/ML**: Ultralytics YOLOv8, EasyOCR, OpenCV, PyTorch
-   **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)

## 🚀 Installation & Setup

### Prerequisites
-   Python 3.8 or higher
-   Pip (Python Package Manager)

### 1. Clone/Download the Repository
Ensure you have the project files in a directory (e.g., `d:/object`).

### 2. Backend Setup
Navigate to the backend directory and install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

*Note: This installs `ultralytics`, `easyocr`, `fastapi`, `uvicorn`, and other necessary libraries. It may take a few minutes.*

## 🏃‍♂️ How to Run

1.  **Start the Server**:
    From the `backend` directory, run:
    ```bash
    uvicorn main:app --reload
    ```
    *On the first run, the system will automatically download the YOLOv8m model weights (~50MB).*

2.  **Open the Application**:
    Open your web browser and navigate to:
    [http://localhost:8000/](http://localhost:8000/)

## 📖 Usage Guide

1.  **Upload**: Drag and drop an image onto the upload zone or click "Browse Files".
2.  **Analyze**: The system processes the image instantly.
3.  **Explore**:
    -   **Hover** over the image to see bounding boxes light up.
    -   **Read** the "Analysis Results" panel for detailed object info and OCR text.
    -   **Check** the "Overview" card for a quick summary.
4.  **Search**: Use the search bar to find specific items (e.g., type "car" or text found in the image).
5.  **Reset**: Click "New Upload" to analyze another image.

## 📂 Project Structure

```
/
├── backend/
│   ├── main.py          # FastAPI application & endpoints
│   ├── detector.py      # YOLOv8 Object Detection wrapper
│   ├── ocr.py           # EasyOCR wrapper
│   └── requirements.txt # Python dependencies
└── frontend/
    ├── index.html       # Main user interface
    ├── style.css        # Styling and animations
    └── script.js        # Frontend logic and API integration
```
