import mysql.connector

try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="faceid",
        password="abc123",
        database="faceid",
    )
    print("✅ Kết nối MySQL thành công!")
    cur = conn.cursor()
    cur.execute("SHOW TABLES;")
    print("Bảng:", [r[0] for r in cur.fetchall()])
    conn.close()
except mysql.connector.Error as err:
    print(f"❌ Lỗi: {err}")
