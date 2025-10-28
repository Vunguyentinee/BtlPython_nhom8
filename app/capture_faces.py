# app/capture_faces.py
import cv2, os

FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def capture_images(ma_nv: str, hoten: str, samples: int = 30, camera_index: int = 0):
    """
    Chụp ảnh khuôn mặt, cắt & lưu ảnh xám 200x200 vào dataset/<ma_nv>/
    Nhấn SPACE để chụp, ESC để thoát sớm.
    """
    save_dir = os.path.join("dataset", ma_nv)
    os.makedirs(save_dir, exist_ok=True)

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ Không mở được camera. Thử camera_index=1 hoặc kiểm tra quyền camera.")
        return

    count = 0
    print(f"📸 Bắt đầu chụp cho {hoten} ({ma_nv}) — lưu vào {save_dir}")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = FACE_CASCADE.detectMultiScale(gray, 1.3, 5)

        # vẽ khung & hiển thị
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

        cv2.putText(frame, f"{ma_nv} | {hoten} | {count}/{samples}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.imshow("SPACE = chụp | ESC = thoát", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            break
        elif key == 32 and len(faces) > 0:  # SPACE
            # Lấy mặt đầu tiên, cắt 200x200 xám
            (x, y, w, h) = faces[0]
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (200, 200))
            out_path = os.path.join(save_dir, f"{ma_nv}_{count:03d}.png")
            cv2.imwrite(out_path, face_img)
            print(f"✅ Lưu {out_path}")
            count += 1
            if count >= samples:
                break

    cap.release()
    cv2.destroyAllWindows()
    print(f"🟢 Hoàn tất — đã chụp {count}/{samples} ảnh cho {ma_nv}")

if __name__ == "__main__":
    # Prompt nhập nhanh khi chạy: python -m app.capture_faces
    try:
        ma = input("Nhập mã nhân viên (vd NV01): ").strip()
        ten = input("Nhập họ tên (vd Nguyen Van A): ").strip()
        so = input("Số ảnh cần chụp (mặc định 30): ").strip()
        so = int(so) if so else 30
        cam = input("Camera index (mặc định 0): ").strip()
        cam = int(cam) if cam else 0
        capture_images(ma, ten, samples=so, camera_index=cam)
    except KeyboardInterrupt:
        pass
