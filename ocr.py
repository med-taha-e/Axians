import cv2
import pytesseract
import numpy as np
from collections import Counter
import time
import os

pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'  

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 30, 150)
    dilated = cv2.dilate(edged, None, iterations=2)
    return dilated

def detect_text_regions(image):
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area, max_area = 100, 10000
    aspect_ratio_range = (1.5, 10)  
    text_regions = []
    
    for c in contours:
        area = cv2.contourArea(c)
        if min_area < area < max_area:
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = w / float(h)
            if aspect_ratio_range[0] < aspect_ratio < aspect_ratio_range[1]:
                text_regions.append((x, y, w, h))
    
    return text_regions

def validate_text(text):
    # Remove non-alphanumeric characters
    #cleaned_text = ''.join(c for c in text if c.isalnum() or c.isspace())
    cleaned_text = ''.join(c for c in text if c.isalnum() or c in 'éèàùâêîôûëïüÿçÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ' or c.isspace())
    # Check if the cleaned text has a minimum length and contains at least one letter
    return len(cleaned_text) >= 3 and any(c.isalpha() for c in cleaned_text)

def write_to_file(text, filename):
    with open(filename, 'a') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30) 
    text_buffer = []
    buffer_size = 10
    
    output_dir = 'ocr_output'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"ocr_output_{time.strftime('%Y%m%d_%H%M%S')}.txt")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        preprocessed = preprocess_image(frame)
        text_regions = detect_text_regions(preprocessed)
        
        frame_texts = []

        for (x, y, w, h) in text_regions:
            roi = frame[y:y+h, x:x+w]
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            roi_thresh = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            text = pytesseract.image_to_string(roi_thresh, config='--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789éèàùâêîôûëïüÿçÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ')
            
            if validate_text(text):
                frame_texts.append(text.strip())
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        text_buffer.append(frame_texts)
        if len(text_buffer) > buffer_size:
            text_buffer.pop(0)

        # Only display and write text that appears consistently
        consistent_texts = [item for sublist in text_buffer for item in sublist]
        text_counts = Counter(consistent_texts)
        for text, count in text_counts.items():
            if count >= buffer_size // 2:
                print(f"Detected Text: {text}")
                write_to_file(text, output_file)

        cv2.imshow('Webcam', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()