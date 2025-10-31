# remove_person.py
import pickle
import shutil
from pathlib import Path
import mysql.connector

# ========== CẤU HÌNH ==========
ROOT = Path(r"E:\BTL_Python")
OUT_PKL = ROOT / "encodings" / "encodings_dlib20.pkl"
DATASET_ROOT = ROOT / "dataset"     # thư mục ảnh
ALSO_DELETE_DATASET = True          # đặt False nếu không muốn xóa ảnh

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "21092005",
    "database": "dulieu_app",
    "port": 3306,
    "autocommit": True,
}

# ========== TIỆN ÍCH ==========
def split_name_id(s: str):
    """Trả về (ten, ma_nv). Nếu input chỉ là mã NV thì (None, ma)."""
    s = s.strip()
    if "_" in s:
        a, b = s.rsplit("_", 1)
        return a.strip(), b.strip()
    # Không có "_" => coi như nhập mã NV
    return None, s

def db_conn():
    return mysql.connector.connect(**DB_CONFIG)

# ========== ENCODINGS ==========
def remove_from_encodings(person_name_or_id: str) -> int:
    """
    Xóa tất cả vectors khớp:
      - nếu nhập 'Ten_Ma' => so sánh theo full label (không phân biệt hoa thường)
      - nếu nhập chỉ 'Ma'  => xóa mọi label có ID đó ở đuôi
    Trả về số vector đã xóa.
    """
    if not OUT_PKL.exists():
        print("❌ Không tìm thấy file encodings:", OUT_PKL)
        return 0

    with open(OUT_PKL, "rb") as f:
        data = pickle.load(f)

    names = list(data.get("names", []))
    embeddings = data.get("embeddings")
    if embeddings is None:
        print("❌ File encodings không hợp lệ (thiếu 'embeddings').")
        return 0

    ten, ma = split_name_id(person_name_or_id)
    keep_idx = []

    if ten is not None:  # có Ten_Ma
        target = f"{ten}_{ma}".lower()
        for i, n in enumerate(names):
            if n.lower() != target:
                keep_idx.append(i)
    else:  # chỉ có Ma
        target_id = ma.lower()
        for i, n in enumerate(names):
            # tách id theo hậu tố sau '_' nếu có
            pid = n.rsplit("_", 1)[-1].lower() if "_" in n else ""
            if pid != target_id:
                keep_idx.append(i)

    removed = len(names) - len(keep_idx)
    if removed == 0:
        print(f"⚠️ Không tìm thấy '{person_name_or_id}' trong encodings.")
        return 0

    # cập nhật và ghi lại
    names_new = [names[i] for i in keep_idx]
    embeddings_new = embeddings[keep_idx]

    with open(OUT_PKL, "wb") as f:
        pickle.dump({"names": names_new, "embeddings": embeddings_new}, f)

    print(f"✅ Đã xoá {removed} vector của '{person_name_or_id}' khỏi {OUT_PKL.name}")
    return removed

# ========== DATABASE ==========
def delete_employee_in_db(person_name_or_id: str) -> int:
    """
    Xóa nhân viên trong DB dựa trên mã NV (khuyến nghị).
    - Nếu nhập Ten_Ma => lấy 'Ma'.
    - Nếu nhập chỉ 'Ma' => dùng luôn.
    Trả về số hàng bị ảnh hưởng (0/1).
    """
    ten, ma = split_name_id(person_name_or_id)
    if not ma:
        print("⚠️ Không xác định được mã NV để xóa trong DB.")
        return 0

    sql = "DELETE FROM nhanvien WHERE ma_nv=%s"
    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (ma,))
                affected = cur.rowcount
        if affected:
            # nhờ ON DELETE CASCADE, chamcong cũng bị xóa theo
            print(f"🗑️  Đã xóa nhân viên ma_nv='{ma}' trong DB (và các bản ghi chấm công nếu có).")
        else:
            print(f"ℹ️ Không thấy ma_nv='{ma}' trong DB.")
        return affected
    except mysql.connector.Error as e:
        print("❌ Lỗi MySQL khi xóa:", e)
        return 0

# ========== DATASET ==========
def delete_dataset_folder(person_name_or_id: str) -> bool:
    """
    Xóa thư mục dataset theo:
      - nếu nhập Ten_Ma => xóa đúng thư mục đó
      - nếu chỉ nhập Ma  => tìm tất cả thư mục có hậu tố _Ma và xóa
    """
    ten, ma = split_name_id(person_name_or_id)
    deleted_any = False

    if ten is not None:
        folder = DATASET_ROOT / f"{ten}_{ma}"
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
            print(f"🗂️  Đã xóa thư mục dataset: {folder}")
            deleted_any = True
        else:
            print(f"ℹ️ Không thấy thư mục: {folder}")
    else:
        # tìm tất cả thư mục kết thúc bằng _<ma>
        if DATASET_ROOT.exists():
            for p in DATASET_ROOT.iterdir():
                if p.is_dir() and p.name.lower().endswith("_" + ma.lower()):
                    shutil.rmtree(p, ignore_errors=True)
                    print(f"🗂️  Đã xóa thư mục dataset: {p}")
                    deleted_any = True
        if not deleted_any:
            print(f"ℹ️ Không tìm thấy thư mục nào có mã '{ma}' trong {DATASET_ROOT}")

    return deleted_any

# ========== MAIN ==========
if __name__ == "__main__":
    person = input("👤 Nhập 'Tên_MãNV' hoặc chỉ 'MãNV' cần xoá: ").strip()
    if not person:
        print("❌ Thiếu đầu vào.")
        raise SystemExit

    # 1) Xóa khỏi encodings
    remove_from_encodings(person)

    # 2) Xóa trong DB (bảng nhanvien; chamcong sẽ CASCADE)
    delete_employee_in_db(person)

    # 3) (tuỳ chọn) Xóa thư mục ảnh dataset
    if ALSO_DELETE_DATASET:
        delete_dataset_folder(person)

    print("🎯 Hoàn tất.")
