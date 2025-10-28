# app/attendance.py
import cv2
import os
import time
import numpy as np
from datetime import datetime
import mysql.connector
from .config import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME

# Kết nối MySQL
def connect_db():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

# Hàm ghi chấm công
def log_attendance(ma_nv, loai):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO chamcong (ma_nv, thoigian, loai) VALUES (%s, %s, %s)",
                (ma_nv, datetime.now(), loai))
    conn.commit()
    conn.close()
    print(f"🟢 Ghi chấm công: {ma_nv} - {loai} lúc {datetime.now()}")

# Hàm xử lý nhận diện khuôn mặt
def check_in_or_out(model_path="models/lbph_model.xml", label_path="models/labels.json"):
    import json

    # Kiểm tra file model & labels
    if not os.path.exists(model_path) or not os.path.exists(label_path):
        print("❌ Chưa có model hoặc labels! Vui lòng train trước.")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)

    with open(label_path, "r") as f:
        labels = json.load(f)

    label_to_ma = {int(v): k for k, v in labels.items()}

    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    print("🟢 Bắt đầu chấm công (Nhấn ESC để thoát)")
    last_check = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            roi_gray = cv2.resize(roi_gray, (200, 200))
            id_, conf = recognizer.predict(roi_gray)

            if conf < 70:  # Ngưỡng nhận diện (LBPH_THRESHOLD trong config)
                ma_nv = label_to_ma.get(id_, "Unknown")

                # Hiển thị
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
                cv2.putText(frame, f"{ma_nv} ({conf:.1f})", (x,y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

                # Tránh ghi liên tục — mỗi NV cách nhau >= 15s
                now = time.time()
                if ma_nv != "Unknown":
                    if ma_nv not in last_check or now - last_check[ma_nv] > 15:
                        loai = "vao" if ma_nv not in last_check else "ra"
                        log_attendance(ma_nv, loai)
                        last_check[ma_nv] = now

            else:
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255), 2)
                cv2.putText(frame, "Unknown", (x,y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

        cv2.imshow("Cham cong - ESC de thoat", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("🟡 Dừng chấm công.")

