# encode_manager.py
import os, sys, pickle, time
from pathlib import Path
import numpy as np

from config import ROOT, ENCODINGS_PKL
from remove_person import (
    remove_from_encodings,
    delete_employee_in_db,
    delete_dataset_folder,
    ALSO_DELETE_DATASET,
)

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def pause():
    input("\nNhấn Enter để quay lại menu...")

# ====== CÁC CHỨC NĂNG CHÍNH ======

def encode_full():
    """Encode lại toàn bộ dataset từ đầu (sử dụng encoding_face.py)."""
    print("⚙️ Đang chạy encode toàn bộ dataset (mất vài phút)...\n")
    os.system(f'python "{ROOT / "encoding_face.py"}"')
    pause()

def encode_sync():
    """Đồng bộ thông minh (tự thêm / xóa / cập nhật)."""
    print("🔄 Đang chạy encode đồng bộ thông minh...\n")
    os.system(f'python "{ROOT / "encode_sync.py"}"')
    pause()

def remove_person():
    """Xóa 1 người cụ thể khỏi file encodings, Database và Dataset."""
    if not ENCODINGS_PKL.exists():
        print("❌ Không tìm thấy file encodings_dlib20.pkl")
        pause()
        return
    person = input("👤 Nhập 'Tên_MãNV' hoặc chỉ 'MãNV' cần xoá: ").strip()
    if not person:
        print("⚠️ Đầu vào không hợp lệ.")
        pause()
        return

    print("\n⚠️ CẢNH BÁO: Thao tác này sẽ XÓA VĨNH VIỄN và KHÔNG THỂ HOÀN TÁC:")
    print(f"   - Vector khuôn mặt của '{person}' trong file encodings")
    print(f"   - Bản ghi nhân viên '{person}' trong DB (kèm toàn bộ lịch sử chấm công)")
    if ALSO_DELETE_DATASET:
        print(f"   - Toàn bộ ảnh dataset (raw/processed) của '{person}'")
    confirm = input(f"\nGõ lại chính xác '{person}' để xác nhận xóa (Enter để hủy): ").strip()
    if confirm != person:
        print("❌ Đã hủy thao tác xóa.")
        pause()
        return

    # 1) Xóa khỏi encodings (remove_from_encodings tự xử lý cả 2 dạng: full label và chỉ mã NV)
    remove_from_encodings(person)

    # 2) Xóa trong DB (bảng nhanvien; chamcong sẽ CASCADE)
    delete_employee_in_db(person)

    # 3) Xóa thư mục ảnh dataset (chỉ khi được phép qua ALSO_DELETE_DATASET)
    if ALSO_DELETE_DATASET:
        delete_dataset_folder(person)
    else:
        print("ℹ️ Bỏ qua xóa thư mục dataset (ALSO_DELETE_DATASET=False).")

    print("🎯 Hoàn tất quá trình xóa nhân viên.")
    pause()

def info_file():
    """In thông tin chi tiết file encodings."""
    if not ENCODINGS_PKL.exists():
        print("❌ Không tìm thấy file encodings_dlib20.pkl")
        pause()
        return
    data = pickle.load(open(ENCODINGS_PKL, "rb"))
    names = np.array(data["names"])
    embeddings = np.array(data["embeddings"])
    unique, counts = np.unique(names, return_counts=True)

    print("📊 THÔNG TIN FILE ENCODINGS:")
    print(f"📁 Đường dẫn: {ENCODINGS_PKL}")
    print(f"👥 Tổng vector: {len(names)}")
    print(f"📏 Kích thước embedding: {embeddings.shape}")
    print("\n🧩 Danh sách người:")
    for u, c in zip(unique, counts):
        print(f"   - {u}: {c} vector")
    pause()

# ====== MENU CHÍNH ======
def main_menu():
    while True:
        clear()
        print("===============================")
        print("👤 FACE ENCODE MANAGER")
        print("===============================")
        print("[1] Encode toàn bộ từ đầu")
        print("[2] Đồng bộ thông minh (thêm / xóa / cập nhật)")
        print("[3] Xóa 1 người khỏi file encodings")
        print("[4] Kiểm tra thông tin file .pkl")
        print("[0] Thoát")
        print("===============================")
        choice = input("Chọn thao tác: ").strip()

        if choice == "1": encode_full()
        elif choice == "2": encode_sync()
        elif choice == "3": remove_person()
        elif choice == "4": info_file()
        elif choice == "0":
            print("👋 Thoát chương trình.")
            time.sleep(1)
            break
        else:
            print("⚠️ Lựa chọn không hợp lệ.")
            time.sleep(1)

if __name__ == "__main__":
    main_menu()
