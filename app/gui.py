import tkinter as tk
from tkinter import ttk, messagebox
import app.db as db

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FaceID Attendance — Desktop")
        self.root.geometry("900x600")

        # --- Frame thông tin nhân viên ---
        self.frame_nv = tk.Frame(self.root)
        self.frame_nv.pack(pady=10)

        tk.Label(self.frame_nv, text="Mã").grid(row=0, column=0)
        tk.Label(self.frame_nv, text="Tên").grid(row=0, column=2)
        tk.Label(self.frame_nv, text="Phòng").grid(row=1, column=0)
        tk.Label(self.frame_nv, text="Chức danh").grid(row=1, column=2)

        self.ma_nv = tk.Entry(self.frame_nv)
        self.hoten = tk.Entry(self.frame_nv)
        self.phong = tk.Entry(self.frame_nv)
        self.chucvu = tk.Entry(self.frame_nv)

        self.ma_nv.grid(row=0, column=1, padx=5)
        self.hoten.grid(row=0, column=3, padx=5)
        self.phong.grid(row=1, column=1, padx=5)
        self.chucvu.grid(row=1, column=3, padx=5)

        tk.Button(self.frame_nv, text="Thêm nhân viên", command=self.add_employee).grid(row=2, column=0, columnspan=2, pady=5)
        tk.Button(self.frame_nv, text="Tải danh sách", command=self.load_employees).grid(row=2, column=2, columnspan=2, pady=5)

        # --- Bảng Treeview hiển thị nhân viên ---
        columns = ("code", "name", "dept", "title")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180)
        self.tree.pack(fill=tk.BOTH, expand=True)

        db.ensure_tables()
        self.root.mainloop()

    # === Thêm nhân viên ===
    def add_employee(self):
        ma = self.ma_nv.get().strip()
        ten = self.hoten.get().strip()
        pb = self.phong.get().strip()
        cv = self.chucvu.get().strip()

        if not ma or not ten:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập mã và tên nhân viên")
            return

        try:
            db.employee_create(ma, ten, pb, cv)
            messagebox.showinfo("Thành công", "Đã thêm nhân viên mới!")
        except Exception as e:
            messagebox.showerror("DB", f"Lỗi: {e}")

    # === Tải danh sách nhân viên ===
    def load_employees(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            data = db.employee_list()
            for row in data:
                self.tree.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("DB", f"Lỗi tải danh sách: {e}")

if __name__ == "__main__":
    App()
