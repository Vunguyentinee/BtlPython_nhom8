# app/db.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from .config import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME

# ---------- Kết nối ----------
def connect_db():
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME
    )

# ---------- Khởi tạo bảng ----------
def ensure_tables():
    try:
        conn = connect_db(); cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS nhanvien (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ma_nv VARCHAR(20) UNIQUE,
            hoten VARCHAR(100),
            phongban VARCHAR(50),
            chucvu VARCHAR(50),
            ngayvaolam DATE DEFAULT (CURRENT_DATE),
            trangthai TINYINT DEFAULT 1
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS chamcong (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ma_nv VARCHAR(20),
            thoigian DATETIME,
            loai VARCHAR(10),
            FOREIGN KEY (ma_nv) REFERENCES nhanvien(ma_nv)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS taikhoan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(255),
            role ENUM('admin','user') DEFAULT 'user'
        );
        """)

        conn.commit()
    finally:
        try: cur.close(); conn.close()
        except: pass
    print("🟢 Đảm bảo các bảng tồn tại (OK).")

# ---------- CRUD nhân viên ----------
def employee_create(ma_nv: str, hoten: str, phongban: str = "", chucvu: str = ""):
    """Thêm nhân viên mới."""
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO nhanvien (ma_nv, hoten, phongban, chucvu) VALUES (%s,%s,%s,%s)",
            (ma_nv, hoten, phongban, chucvu)
        )
        conn.commit()
        return cur.rowcount
    finally:
        cur.close(); conn.close()

def employee_list():
    """Trả về danh sách nhân viên cho GUI (code, name, dept, title)."""
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT ma_nv, hoten, phongban, chucvu FROM nhanvien ORDER BY ma_nv;")
        return cur.fetchall()
    finally:
        cur.close(); conn.close()

# (Giữ alias nếu ở nơi khác đã dùng plural)
def employees_list():
    return employee_list()

def employee_delete(ma_nv: str):
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM nhanvien WHERE ma_nv=%s", (ma_nv,))
        conn.commit()
        return cur.rowcount
    finally:
        cur.close(); conn.close()

# ---------- Chấm công / Báo cáo ----------
def attendance_insert(ma_nv: str, loai: str):
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO chamcong (ma_nv, thoigian, loai) VALUES (%s,%s,%s)",
            (ma_nv, datetime.now(), loai)
        )
        conn.commit()
        return cur.rowcount
    finally:
        cur.close(); conn.close()

def attendance_today():
    """Trả về log hôm nay để xuất CSV."""
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute("""
            SELECT c.ma_nv, n.hoten, n.phongban, n.chucvu, c.thoigian, c.loai
            FROM chamcong c
            JOIN nhanvien n ON n.ma_nv = c.ma_nv
            WHERE DATE(c.thoigian) = CURDATE()
            ORDER BY c.thoigian ASC;
        """)
        return cur.fetchall()
    finally:
        cur.close(); conn.close()
