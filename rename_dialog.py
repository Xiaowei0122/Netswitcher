# rename_dialog.py - 重命名对话框类
import tkinter as tk
from tkinter import ttk
import os
from utils import get_center_position

class RenameDialog(tk.Toplevel):
    def __init__(self, parent, title, old_name):
        super().__init__(parent)
        self.result = None
        self.transient(parent)
        self.grab_set()
        self.title(title)
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "network.ico")
        try:
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"无法加载图标: {e}")
        
        # 继承主窗口样式
        self.bg_color = parent.bg_color
        self.accent_color = parent.accent_color
        self.button_bg = parent.button_bg
        self.text_color = parent.text_color
        self.header_font = parent.header_font
        self.normal_font = parent.normal_font
          # 设置窗口尺寸
        width = 350
        height = 200
        
        # 计算居中位置
        x, y = get_center_position(parent, width, height)
        
        # 直接设置窗口位置和大小（不会闪烁）
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        self.configure(bg=self.bg_color)
        
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=15)
        
        # 标题部分
        ttk.Label(main_frame, 
                 text="重命名网络配置",
                 font=self.header_font,
                 foreground=self.accent_color).pack(pady=(0, 15))
        
        # 当前名称显示
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill='x', pady=5)
        ttk.Label(name_frame, text="当前名称:").pack(side='left')
        ttk.Label(name_frame, text=old_name, foreground='blue', font=('Microsoft YaHei UI', 9, 'bold')).pack(side='left', padx=5)
        
        # 新名称输入
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill='x', pady=10)
        ttk.Label(input_frame, text="新名称:").pack(side='left')
        
        self.entry = ttk.Entry(input_frame, width=25)
        self.entry.pack(side='left', padx=5, fill='x', expand=True)
        self.entry.insert(0, old_name)
        self.entry.selection_range(0, tk.END)
        self.entry.focus_set()
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(15, 5))
        
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side='right', padx=5)
        ttk.Button(button_frame, text="确定", style="Accent.TButton", command=self.ok).pack(side='right', padx=5)
        
        # 绑定回车键
        self.bind("<Return>", lambda event: self.ok())
        self.bind("<Escape>", lambda event: self.cancel())
        
        # 等待窗口关闭
        self.wait_window(self)
    
    def ok(self):
        self.result = self.entry.get()
        self.destroy()
        
    def cancel(self):
        self.result = None
        self.destroy()
