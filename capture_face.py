import cv2
import os
import numpy as np
import time
import json
import mysql.connector
from datetime import datetime
from pathlib import Path
import re
import sys

ROOT = Path(r"E:\BTL_Python")

# ===================== CONFIG =====================
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "21092005",
    "database": "dulieu_app",
    "port": 3306,
    "autocommit": True,
}

# ===================== MYSQL HELPER =====================
def db_conn():
    return mysql.connector.connect(**DB_CONFIG)

def insert_employee(ma_nv, ten, phongban, chucvu, email, sdt):
    """Chèn nhân viên mới nếu chưa có"""
    sql_check = "SELECT 1 FROM nhanvien WHERE ma_nv=%s LIMIT 1"
    sql_insert = """
        INSERT INTO nhanvien (ma_nv, ten, phongban, chucvu, email, sdt)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_check, (ma_nv,))
            if cur.fetchone():
                print(f"⚠️ Mã nhân viên {ma_nv} đã tồn tại — bỏ qua thêm mới.")
            else:
                cur.execute(sql_insert, (ma_nv, ten, phongban, chucvu, email, sdt))
                print(f"✅ Đã thêm nhân viên mới: {ten} ({ma_nv})")

def safe_slug(s: str) -> str:
    bad = '<>:"/\\|?*'
    return "".join(c for c in s if c not in bad).strip().rstrip(".")

# ===================== FACE COLLECTOR =====================
class FaceCollector:
    def __init__(self,
                 max_images=10,
                 min_area=20000,
                 max_area=100000,
                 radius=120,
                 blur_threshold=60,
                 capture_delay=1.0,
                 preview_size=150,
                 save_root=None):
        self.MAX_IMAGES = max_images
        self.MIN_AREA = min_area
        self.MAX_AREA = max_area
        self.RADIUS = radius
        self.DELAY = capture_delay
        self.BLUR_THRESHOLD = blur_threshold
        self.PREVIEW_SIZE = preview_size
        self.SAVE_ROOT = Path(save_root)
        if not self.SAVE_ROOT.is_absolute():
            # ép relative -> tuyệt đối theo file capture_face
            base = Path(__file__).resolve().parent
            self.SAVE_ROOT = (base / self.SAVE_ROOT).resolve()
        print("📂 Ảnh sẽ lưu vào:", self.SAVE_ROOT)

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        self.last_capture = 0

    # ===================== QUALITY =====================
    def blur_score(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def enhance_preview(self, img):
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = self.clahe.apply(l)
        enhanced = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
        enhanced = cv2.convertScaleAbs(enhanced, alpha=1.6, beta=50)
        return enhanced

    def quality_score(self, face_img):
        blur = min(self.blur_score(face_img) / self.BLUR_THRESHOLD, 1.0)
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        brightness = 1.0 - abs(np.mean(gray) - 127) / 127
        contrast = np.std(gray) / 128
        return float((blur + brightness + contrast) / 3)

    # ===================== UI =====================
    def draw_ui(self, frame, msg, count, quality=None):
        h, w = frame.shape[:2]
        center = (w // 2, h // 2)

        cv2.circle(frame, center, self.RADIUS, (0, 255, 0), 2)
        progress = count / self.MAX_IMAGES
        cv2.rectangle(frame, (50, h - 60), (w - 50, h - 40), (90, 90, 90), -1)
        cv2.rectangle(frame, (50, h - 60), (50 + int((w - 100) * progress), h - 40), (0, 255, 0), -1)

        cv2.putText(frame, msg, (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(frame, f"{count}/{self.MAX_IMAGES}", (30, h - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if quality is not None:
            color = (0, 255, 0) if quality > 0.7 else (0, 255, 255) if quality > 0.5 else (0, 0, 255)
            cv2.putText(frame, f"Quality: {quality:.2f}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # ===================== MAIN COLLECT =====================
    def collect(self, name):
        name = re.sub(r'[<>:"/\\|?*]', '_', name.strip())
        if not name:
            print("❌ Name required")
            return False

        person_root = self.SAVE_ROOT / name
        raw_dir = person_root / "raw"
        proc_dir = person_root / "processed"
        raw_dir.mkdir(parents=True, exist_ok=True)
        proc_dir.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)

        count = 0
        stats = {"saved": 0, "rejected": 0}
        print(f"📸 Collecting faces for: {name}")
        print("Controls: Q-quit, SPACE-pause, R-reset")

        paused = False
        while count < self.MAX_IMAGES:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Cannot read from camera")
                    break

                frame = cv2.flip(frame, 1)
                gray = cv2.cvtColor(self.enhance_preview(frame), cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
                msg = "📍 Align face in circle"
                quality = None

                if len(faces) == 1:
                    x, y, fw, fh = faces[0]
                    area = fw * fh
                    h, w = frame.shape[:2]
                    cx, cy = w // 2, h // 2
                    face_center = (x + fw // 2, y + fh // 2)
                    dx, dy = face_center[0] - cx, face_center[1] - cy
                    in_circle = dx * dx + dy * dy <= self.RADIUS * self.RADIUS

                    if in_circle:
                        if self.MIN_AREA <= area <= self.MAX_AREA:
                            face_img = frame[y:y + fh, x:x + fw]
                            quality = self.quality_score(face_img)
                            if time.time() - self.last_capture >= self.DELAY and quality > 0.35:
                                count += 1
                                cv2.imwrite(str(raw_dir / f"{count:04d}.jpg"), face_img)
                                cv2.imwrite(str(proc_dir / f"{count:04d}.jpg"),
                                            cv2.resize(face_img, (self.PREVIEW_SIZE, self.PREVIEW_SIZE)))
                                self.last_capture = time.time()
                                msg = f"✅ Captured {count}"
                                print(f"Saved {count:04d} (Q:{quality:.2f})")
                            else:
                                msg = f"⏳ Ready... Q:{quality:.2f}"
                        else:
                            msg = "📏 Move closer/farther"
                    else:
                        msg = "🎯 Center face in circle"
                elif len(faces) > 1:
                    msg = "👥 Only one face"

                self.draw_ui(frame, msg, count, quality)
                cv2.imshow("Face Collector", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord(" "):
                paused = not paused
                print("⏸️ Paused" if paused else "▶️ Resumed")
            elif key == ord("r"):
                count = 0
                stats = {"saved": 0, "rejected": 0}
                print("🔄 Reset")

        cap.release()
        cv2.destroyAllWindows()

        metadata = {
            "name": name,
            "date": datetime.now().isoformat(),
            "images": count,
            "stats": stats,
        }
        with open(person_root / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Collected {count} images for {name}")
        return count > 0


# ===================== RUN =====================
if __name__ == "__main__":
    print("=== Nhập thông tin nhân viên mới ===")
    ten = input("Họ và tên: ").strip()
    ma_nv = input("Mã nhân viên (VD: NV001): ").strip()
    phongban = input("Phòng ban: ").strip()
    chucvu = input("Chức vụ: ").strip()
    email = input("Email: ").strip()
    sdt = input("SĐT: ").strip()

    if not ten or not ma_nv:
        print("❌ Thiếu họ tên hoặc mã nhân viên!")
        exit()

    insert_employee(ma_nv, ten, phongban, chucvu, email, sdt)

    folder_name = safe_slug(f"{ten}_{ma_nv}") 
    FaceCollector().collect(folder_name)
