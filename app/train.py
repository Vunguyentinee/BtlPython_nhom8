import os, json, cv2
import numpy as np
from .config import DATASET_DIR, MODELS_DIR
from .utils import ensure_dirs

# CẦN gói: opencv-contrib-python (mới có cv2.face)
LBPH = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)

def load_images_and_labels():
    X, y, label_map = [], [], {}
    current = 0
    if not os.path.isdir(DATASET_DIR):
        return X, np.array(y, dtype=np.int32), label_map
    for code in sorted(os.listdir(DATASET_DIR)):
        folder = os.path.join(DATASET_DIR, code)
        if not os.path.isdir(folder):
            continue
        label_map[current] = code
        for name in os.listdir(folder):
            if name.lower().endswith((".png", ".jpg", ".jpeg")):
                path = os.path.join(folder, name)
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue
                X.append(img)
                y.append(current)
        current += 1
    return X, np.array(y, dtype=np.int32), label_map

def train_and_save():
    ensure_dirs()
    X, y, label_map = load_images_and_labels()
    if len(X) == 0:
        raise RuntimeError("Dataset rỗng — hãy thu ảnh trước.")
    LBPH.train(X, y)
    os.makedirs(MODELS_DIR, exist_ok=True)
    LBPH.save(os.path.join(MODELS_DIR, "lbph_model.xml"))
    with open(os.path.join(MODELS_DIR, "labels.json"), "w", encoding="utf-8") as f:
        json.dump(label_map, f, ensure_ascii=False, indent=2)
    return {"classes": label_map}
