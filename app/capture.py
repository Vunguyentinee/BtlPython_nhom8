import cv2, os
from .config import DATASET_DIR
from .utils import ensure_dirs

FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def capture_employee(code: str, samples: int = 30, cam_index: int = 0):
    """Thu ảnh khuôn mặt về thư mục dataset/<code> (ảnh 200x200 grayscale)."""
    ensure_dirs()
    out_dir = os.path.join(DATASET_DIR, code)
    os.makedirs(out_dir, exist_ok=True)

    cap = cv2.VideoCapture(cam_index)
    count = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = FACE_CASCADE.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (200, 200))
            count += 1
            cv2.imwrite(os.path.join(out_dir, f"{code}_{count:03d}.png"), face_img)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.putText(frame, f"Captured: {count}/{samples}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Capture", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC để dừng
            break
        if count >= samples:
            break

    cap.release(); cv2.destroyAllWindows()
    return count
