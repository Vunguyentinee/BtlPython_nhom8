USE dulieu_app;

CREATE TABLE taikhoan (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'STT',
  ten_that VARCHAR(100) NOT NULL COMMENT 'Tên thật',
  ma_nv VARCHAR(20) NOT NULL COMMENT 'Mã nhân viên',
  ten_dang_nhap VARCHAR(50) UNIQUE NOT NULL COMMENT 'Tên đăng nhập',
  mat_khau VARCHAR(255) NOT NULL COMMENT 'Mật khẩu',
  FOREIGN KEY (ma_nv) REFERENCES nhanvien(ma_nv)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);
