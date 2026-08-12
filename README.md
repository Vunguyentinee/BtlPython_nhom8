# Ứng dụng Chấm công nhận diện khuôn mặt

Ứng dụng desktop (Tkinter) chấm công nhân viên bằng nhận diện khuôn mặt (dlib), lưu dữ liệu trong MySQL.

## 1. Yêu cầu

- Python 3.10.6 (khuyến nghị dùng venv — bản dlib đi kèm được build sẵn cho 3.10 trên Windows)
- MySQL Server đang chạy cục bộ (hoặc chỉnh `.env` để trỏ tới server khác)
- Webcam

## 2. Cài đặt

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2.1. Tải model dlib

Tải 3 file sau và đặt vào thư mục `models/`:

1. `shape_predictor_5_face_landmarks.dat` (căn chỉnh khuôn mặt trước khi encode)
   https://github.com/davisking/dlib-models/raw/master/shape_predictor_5_face_landmarks.dat.bz2
   (link dự phòng: https://github.com/ageitgey/face_recognition_models/raw/master/face_recognition_models/models/shape_predictor_5_face_landmarks.dat)

2. `dlib_face_recognition_resnet_model_v1.dat` (mã hóa khuôn mặt thành vector 128 chiều)
   https://github.com/davisking/dlib-models/raw/master/dlib_face_recognition_resnet_model_v1.dat.bz2
   (link dự phòng: https://github.com/ageitgey/face_recognition_models/raw/master/face_recognition_models/models/dlib_face_recognition_resnet_model_v1.dat)

3. `mmod_human_face_detector.dat` (phát hiện khuôn mặt bằng CNN, chính xác hơn HOG với góc nghiêng — hiện chưa bật mặc định, xem `USE_CNN` trong code)
   https://github.com/davisking/dlib-models/raw/master/mmod_human_face_detector.dat.bz2

Các file `.dat.bz2` cần giải nén trước khi đặt vào `models/`.

### 2.2. Tạo database MySQL

Chạy lần lượt (thứ tự quan trọng vì có khóa ngoại):

```bash
mysql -u root -p < nhanvien.sql
mysql -u root -p < chamcong.sql
mysql -u root -p < taikhoan.sql
```

### 2.3. Cấu hình kết nối DB

Copy `.env.example` thành `.env` rồi điền mật khẩu MySQL thật của bạn:

```bash
copy .env.example .env        # Windows
```

`.env` không được commit lên git (đã có trong `.gitignore`).

## 3. Chạy ứng dụng

```bash
python ui.py
```

Lần đầu chạy: bấm **Đăng ký** trên màn hình đăng nhập để tạo tài khoản Admin (ứng dụng không có tài khoản mặc định).

## 4. Cấu trúc thư mục

```
ui.py                   Giao diện chính (Tkinter)
capture_face.py         Thu ảnh khuôn mặt cho nhân viên mới
encoding_face.py        Encode toàn bộ dataset từ đầu
encode_sync.py          Đồng bộ thông minh dataset <-> file encodings
encoding_loaded.py      Nạp & khử trùng lặp vector encodings khi chạy nhận diện
recognize_checkin_out.py  Nhận diện qua camera, tự động check-in/check-out
remove_person.py        Xóa nhân viên khỏi encodings/DB/dataset
encode_manager.py       Menu CLI quản lý file encodings
config.py               Đường dẫn, kết nối DB, hàm slug dùng chung
dataset/<Tên_MãNV>/     Ảnh raw/processed từng nhân viên
models/                 File .dat của dlib (không commit, xem mục 2.1)
encodings/              File .pkl chứa vector khuôn mặt đã encode
```
