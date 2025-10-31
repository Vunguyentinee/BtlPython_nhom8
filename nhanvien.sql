USE dulieu_app;

CREATE TABLE nhanvien (
  STT          INT AUTO_INCREMENT PRIMARY KEY,
  ma_nv       VARCHAR(20) UNIQUE NOT NULL,
  ten         VARCHAR(100) NOT NULL,
  phongban    VARCHAR(100),
  chucvu      VARCHAR(100),       -- thêm trực tiếp vào đây
  ngaysinh    DATE DEFAULT (CURRENT_DATE),
  email       VARCHAR(100),
  sdt         VARCHAR(20)
);