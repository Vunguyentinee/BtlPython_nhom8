USE dulieu_app;

CREATE TABLE chamcong (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'STT',
  ma_nv VARCHAR(20) NOT NULL COMMENT 'Mã nhân viên',
  ten_nv VARCHAR(100) NOT NULL COMMENT 'Tên nhân viên',
  ngay DATE NOT NULL COMMENT 'Ngày chấm công',
  gio_checkin DATETIME DEFAULT NULL COMMENT 'Thời gian check-in',
  gio_checkout DATETIME DEFAULT NULL COMMENT 'Thời gian check-out',
  ghichu VARCHAR(255) DEFAULT NULL COMMENT 'Ghi chú',
  UNIQUE KEY uniq_ngay_nv (ngay, ma_nv),
  FOREIGN KEY (ma_nv) REFERENCES nhanvien(ma_nv)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);
