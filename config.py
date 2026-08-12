# config.py
from pathlib import Path
import os
import re
import unicodedata
import mysql.connector

# ===================== PATH CONFIGURATION =====================
ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset"
ENCODINGS_DIR = ROOT / "encodings"
ENCODINGS_PKL = ENCODINGS_DIR / "encodings_dlib20.pkl"
MODELS_DIR = ROOT / "models"

# Model paths
PREDICTOR_PATH   = MODELS_DIR / "shape_predictor_5_face_landmarks.dat"
RECOG_MODEL_PATH = MODELS_DIR / "dlib_face_recognition_resnet_model_v1.dat"
CNN_PATH         = MODELS_DIR / "mmod_human_face_detector.dat"

# ===================== NAMING HELPERS =====================
def safe_slug(s: str) -> str:
    """
    Chuẩn hóa 'Tên_MãNV' thành tên thư mục/label an toàn:
    bỏ dấu tiếng Việt, chỉ giữ [A-Za-z0-9._-], gộp khoảng trắng thành '_'.
    Đây LÀ hàm duy nhất được dùng để đặt tên thư mục dataset và label trong
    file encodings — mọi nơi tạo/xóa thư mục hoặc vector phải dùng hàm này
    để đảm bảo khớp nhau.
    """
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")
    return s

def split_name_id(s: str):
    """
    Tách 'Ten_MaNV' thành (ten, ma). Nếu không có dấu '_', coi toàn bộ
    chuỗi là mã NV: trả về (None, ma). Dùng chung cho mọi nơi cần tách
    nhãn/khoá tìm kiếm theo định dạng này (encodings, DB, dataset...).
    """
    s = s.strip()
    if "_" in s:
        ten, ma = s.rsplit("_", 1)
        return ten.strip(), ma.strip()
    return None, s

# ===================== ENV LOADING =====================
def _load_env_file(path: Path):
    """Nạp biến môi trường từ file .env (KEY=VALUE mỗi dòng), không ghi đè
    biến đã có sẵn trong môi trường thật."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

_load_env_file(ROOT / ".env")

def _env_int(key: str, default: int) -> int:
    """os.environ.get(key, default) không áp dụng default khi biến tồn tại
    nhưng rỗng (vd. 'DB_PORT=' trong .env) — hàm này xử lý cả trường hợp đó."""
    value = os.environ.get(key, "").strip()
    return int(value) if value else default

# ===================== DATABASE CONFIGURATION =====================
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "dulieu_app"),
    "port": _env_int("DB_PORT", 3306),
    "autocommit": True,
}

def db_conn():
    return mysql.connector.connect(**DB_CONFIG)
