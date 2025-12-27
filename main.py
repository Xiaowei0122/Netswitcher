# main.py - 程序入口点
import tkinter as tk
from tkinter import messagebox

from utils import is_admin
from main_window import SimpleNetworkSwitcher

if __name__ == "__main__":
    if not is_admin():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("权限错误", "请以管理员身份运行此程序")
        root.destroy()
    else:
        app = SimpleNetworkSwitcher()
        app.mainloop()
