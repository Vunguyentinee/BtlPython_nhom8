# recognize_checkin_checkout_fast.py — Dlib-only HOG, lưu MySQL theo bảng của bạn
# Bảng: chamcong(id, ma_nv, ten_nv, ngay, gio_checkin, gio_checkout, ghichu)
# Ghi chú tự động theo mốc 08:00:00 ("OK" nếu đúng/trước giờ, ngược lại "Muộn X phút")

import os
import cv2
import numpy as np
import dlib
import threading
import time
import mysql.connector
from datetime import datetime, date, time as dtime
from collections import defaultdict, deque
from pathlib import Path
from encoding_loaded import load_all_encodings

# =============== CẤU HÌNH ===============
DB_CONFIG = {
    "host": "127.0.0.1",      # 🔧 CÓ THỂ CẦN ĐỔI
    "user": "root",           # 🔧 CÓ THỂ CẦN ĐỔI
    "password": "21092005",     # 🔧 CÓ THỂ CẦN ĐỔI
    "database": "dulieu_app", # 🔧 CÓ THỂ CẦN ĐỔI
    "port": 3306,
    "autocommit": True,
}

def db_conn():
    return mysql.connector.connect(**DB_CONFIG)

TOLERANCE = 0.5
TOLERANCE2 = TOLERANCE * TOLERANCE
FRAME_WIDTH = 640
FRAME_HEIGHT = 360
TARGET_FPS = 30
PROCESS_EVERY = 3
DETECT_SCALE = 0.4
USE_CNN = False

ON_TIME = dtime(8, 0, 0)  # mốc 8h để tính ghi chú

# Model paths
ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / "models"
PREDICTOR_PATH = MODELS_DIR / "shape_predictor_5_face_landmarks.dat"
RECOG_MODEL_PATH = MODELS_DIR / "dlib_face_recognition_resnet_model_v1.dat"
CNN_PATH = MODELS_DIR / "mmod_human_face_detector.dat"

# =============== DLIB INIT ===============
def _require(p: Path, hint: str):
    if not p.exists():  
        raise FileNotFoundError(f"Missing model: {p}\nHint: {hint}")

_require(PREDICTOR_PATH,  "Đặt shape_predictor_5_face_landmarks.dat vào thư mục models/")
_require(RECOG_MODEL_PATH,"Đặt dlib_face_recognition_resnet_model_v1.dat vào thư mục models/")

_hog = dlib.get_frontal_face_detector()
_cnn = dlib.cnn_face_detection_model_v1(str(CNN_PATH)) if USE_CNN and CNN_PATH.exists() else None
PRED = dlib.shape_predictor(str(PREDICTOR_PATH))
REC  = dlib.face_recognition_model_v1(str(RECOG_MODEL_PATH))

# =============== DB HELPER ===============
def db_conn():
    return mysql.connector.connect(**DB_CONFIG)

# =============== TÁCH TÊN & MÃ NV ===============
def split_name_id(full_name: str):
    """
    Chuẩn label ảnh: 'TenNhanVien_maNV'
    Ví dụ: 'Nguyen Van A_nv01' -> ('Nguyen Van A', 'nv01')
    """
    parts = full_name.rsplit("_", 1)  # 🔧 CÓ THỂ CẦN ĐỔI nếu bạn đặt tên khác format
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return full_name.strip(), ""

# =============== TIỆN ÍCH THỜI GIAN ===============
def today_date() -> date:
    return date.today()

def now_datetime_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def now_time_only() -> dtime:
    dt = datetime.now()
    return dtime(dt.hour, dt.minute, dt.second)

def note_from_checkin(now_t: dtime) -> str:
    if now_t <= ON_TIME:
        return "OK"
    late_min = int((datetime.combine(today_date(), now_t) - datetime.combine(today_date(), ON_TIME)).total_seconds() // 60)
    return f"Muộn {late_min} phút"

# =============== TRUY VẤN THEO BẢNG CỦA BẠN ===============
def get_today_row(ma_nv: str):
    sql = """
    SELECT id, ma_nv, ten_nv, ngay, gio_checkin, gio_checkout, ghichu
    FROM chamcong
    WHERE ngay=%s AND ma_nv=%s
    LIMIT 1
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (today_date(), ma_nv))
            row = cur.fetchone()
            if not row:
                return None
            keys = ["id", "ma_nv", "ten_nv", "ngay", "gio_checkin", "gio_checkout", "ghichu"]
            return dict(zip(keys, row))

def insert_checkin(ma_nv: str, ten_nv: str, dt_checkin, ghichu):
    sql = """
    INSERT INTO chamcong (ma_nv, ten_nv, ngay, gio_checkin, gio_checkout, ghichu)
    VALUES (%s, %s, %s, %s, NULL, %s)
    ON DUPLICATE KEY UPDATE
      ten_nv = VALUES(ten_nv),
      gio_checkin = COALESCE(VALUES(gio_checkin), gio_checkin),
      ghichu = VALUES(ghichu)
    """
    params = (ma_nv, ten_nv, today_date(), dt_checkin, ghichu)
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)

def insert_or_update_checkout(ma_nv: str, ten_nv: str, dt_checkout):
    """
    Cập nhật giờ checkout cho nhân viên. Nếu chưa có dòng hôm nay thì thêm mới.
    """
    sql = """
    INSERT INTO chamcong (ma_nv, ten_nv, ngay, gio_checkin, gio_checkout, ghichu)
    VALUES (%s, %s, %s, NULL, %s, NULL)
    ON DUPLICATE KEY UPDATE
        gio_checkout = VALUES(gio_checkout)
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (ma_nv, ten_nv, today_date(), dt_checkout))

def update_checkin(ma_nv: str, dt_checkin, ghichu):
    sql = """
    UPDATE chamcong
    SET gio_checkin=%s, ghichu=%s
    WHERE ngay=%s AND ma_nv=%s
    """
    params = (dt_checkin, ghichu, today_date(), ma_nv)
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)

def update_checkout(ma_nv: str, dt_checkout):
    sql = """
    UPDATE chamcong
    SET gio_checkout=%s
    WHERE ngay=%s AND ma_nv=%s
    """
    params = (dt_checkout, today_date(), ma_nv)
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)


# =============== LOGIC CHECK-IN / CHECK-OUT ===============
def check_in(full_name: str) -> str:
    ten, ma = split_name_id(full_name)
    if not ma:
        return f"⚠️ Không tách được mã NV từ: '{full_name}'. Hãy đặt tên theo 'Ten_maNV'."

    row = get_today_row(ma)
    now_dt = datetime.now()
    note = note_from_checkin(now_dt.time())

    if row is None:
        insert_checkin(ma, ten, now_dt, note)
        return f"✅ CHECK-IN: {ten} ({ma}) @ {now_dt.strftime('%Y-%m-%d %H:%M:%S')} | {note}"
    else:
        if not row["gio_checkin"]:
            update_checkin(ma, now_dt, note)
            return f"✅ CHECK-IN (update): {ten} ({ma}) @ {now_dt.strftime('%Y-%m-%d %H:%M:%S')} | {note}"
        else:
            gc = row["gio_checkin"]
            gc_str = gc.strftime('%Y-%m-%d %H:%M:%S') if gc else 'NULL'
            return f"ℹ️ Đã check-in trước đó: {ten} ({ma}) @ {gc_str}"

def check_out(full_name: str) -> str:
    ten, ma = split_name_id(full_name)
    if not ma:
        return f"⚠️ Không tách được mã NV từ: '{full_name}'. Hãy đặt tên theo 'Ten_maNV'."

    row = get_today_row(ma)
    now_dt = datetime.now() 

    if row is None:
        # chưa có check-in: tạo dòng mới, set checkout; ghichu để trống (hoặc có thể ghi 'Thiếu check-in')
        insert_or_update_checkout(ma, ten, now_dt)
        return f"✅ CHECK-OUT (new row): {ten} ({ma}) @ {now_dt.strftime('%Y-%m-%d %H:%M:%S')} (⚠️ thiếu check-in)"
    else:
        if not row["gio_checkout"]:
            update_checkout(ma, now_dt)
            return f"✅ CHECK-OUT: {ten} ({ma}) @ {now_dt.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            go = row["gio_checkout"]
            go_str = go.strftime('%Y-%m-%d %H:%M:%S') if go else 'NULL'
            return f"ℹ️ Đã check-out trước đó: {ten} ({ma}) @ {go_str}"

# =============== DLIB UTILS ===============
def _detect_rects_small(rgb):
    h, w = rgb.shape[:2]
    small = cv2.resize(rgb, (int(w * DETECT_SCALE), int(h * DETECT_SCALE))) if DETECT_SCALE != 1.0 else rgb
    if _cnn is not None:
        dets = _cnn(small, 0)
        rects_small = [d.rect for d in dets]
    else:
        rects_small = _hog(small, 0)
    if DETECT_SCALE == 1.0:
        return list(rects_small)
    inv = 1.0 / DETECT_SCALE
    rects = []
    for r in rects_small:
        rects.append(dlib.rectangle(int(r.left()*inv), int(r.top()*inv), int(r.right()*inv), int(r.bottom()*inv)))
    return rects

def _encode_one_rgb(rgb, rect):
    shape = PRED(rgb, rect)
    vec = REC.compute_face_descriptor(rgb, shape, num_jitters=0)
    return np.asarray(vec, dtype=np.float32)

# =============== CAMERA THREAD ===============
class CameraReader:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.q = deque(maxlen=1)
        self.stopped = False
        self.t = threading.Thread(target=self._update, daemon=True)
        self.t.start()

    def _update(self):
        while not self.stopped:
            ok, frame = self.cap.read()
            if ok:
                self.q.append(frame)

    def read(self):
        return self.q[-1] if self.q else None

    def release(self):
        self.stopped = True
        time.sleep(0.05)
        self.cap.release()

# =============== MAIN LOOP ===============
def main():
    known_encodings, known_names = load_all_encodings()
    if not isinstance(known_encodings, np.ndarray):
        known_encodings = np.array(known_encodings, dtype=np.float32)
    else:
        known_encodings = known_encodings.astype(np.float32, copy=False)
    known_names = np.array(known_names)

    if known_encodings.size == 0:
        print("❌ Không có dữ liệu encodings. Hãy encode trước.")
        return

    cam = CameraReader(0)
    time.sleep(0.15)

    print("🎥 Camera sẵn sàng. Auto check-in/out (mỗi người ≥60s/lần). Nhấn [q] để thoát.")
    last_action_time = defaultdict(lambda: datetime.min)
    i = 0
    boxes_cache = []

    while True:
        frame = cam.read()
        if frame is None:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if i % PROCESS_EVERY == 0:
            rects = _detect_rects_small(rgb)
            boxes_cache = []
            for rect in rects:
                l, t, rgt, btm = rect.left(), rect.top(), rect.right(), rect.bottom()
                if l < 0 or t < 0 or rgt <= l or btm <= t:
                    continue

                vec = _encode_one_rgb(rgb, rect)
                diff = known_encodings - vec
                d2 = np.einsum('ij,ij->i', diff, diff)
                min_idx = int(np.argmin(d2)) if d2.size else None

                name = "Unknown"
                color = (0, 0, 255)

                if min_idx is not None and d2[min_idx] <= TOLERANCE2:
                    name = str(known_names[min_idx])
                    color = (0, 255, 0)

                    now = datetime.now()
                    if (now - last_action_time[name]).total_seconds() >= 60:
                        ten, ma = split_name_id(name)
                        msg = None
                        row = get_today_row(ma)
                        if row is None or not row.get("gio_checkin"):
                            msg = check_in(name)
                        elif not row.get("gio_checkout"):
                            msg = check_out(name)
                        else:
                            msg = f"ℹ️ {name} đã check-in & check-out hôm nay."
                        print(msg)
                        last_action_time[name] = now

                boxes_cache.append((rect, name, color))

        # Vẽ khung & nhãn
        for rect, name, color in boxes_cache:
            l, t, rgt, btm = rect.left(), rect.top(), rect.right(), rect.bottom()
            cv2.rectangle(frame, (l, t), (rgt, btm), color, 2)
            if name != "Unknown":
                ten, ma = split_name_id(name)
                label = f"{ten} ({ma})" if ma else ten
            else:
                label = name
            cv2.putText(frame, label, (l, t - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        h, w = frame.shape[:2]
        cv2.putText(frame, "AUTO MODE (>=60s) - press [q] to quit",
                    (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 220, 50), 2)

        cv2.imshow("Attendance - FAST (MySQL, chamcong)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

        i += 1

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
