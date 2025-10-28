import os, json, cv2
from .config import MODELS_DIR, LBPH_THRESHOLD

class Recognizer:
    def __init__(self):
        self.model = cv2.face.LBPHFaceRecognizer_create()
        self.model.read(os.path.join(MODELS_DIR, "lbph_model.xml"))
        with open(os.path.join(MODELS_DIR, "labels.json"), "r", encoding="utf-8") as f:
            self.label_map = {int(k): v for k, v in json.load(f).items()}

    def predict_code(self, face_gray_200):
        """Nhận vào ảnh xám kích thước 200x200; trả về (mã_nv|None, confidence)."""
        label, confidence = self.model.predict(face_gray_200)
        code = self.label_map.get(label)
        if code is not None and confidence <= LBPH_THRESHOLD:
            return code, confidence
        return None, confidence
