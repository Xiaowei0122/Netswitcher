# main_window.py - 主窗口类
import tkinter as tk
from tkinter import ttk, messagebox, font
import os
import json
from functools import partial

from config_window import ConfigWindow
from rename_dialog import RenameDialog
from utils import (
    is_admin, get_active_interfaces, get_network_interfaces,
    set_static_ip, set_dhcp, enable_interface, disable_interface,
    center_window
)

CONFIG_FILE = "network_config.json"

class SimpleNetworkSwitcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("网络一键切换器")
        self.resizable(False,False)
        self.geometry("450x380")
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "network.ico")
        try:
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"无法加载图标: {e}")
            
        # 配色方案
        self.bg_color = '#f5f5f5'  # 浅灰色背景
        self.accent_color = '#2196F3'  # 蓝色强调色
        self.accent_hover = '#1976D2'  # 深蓝色悬停
        self.button_bg = '#ffffff'  # 按钮背景色
        self.text_color = '#212121'  # 深灰色文字
        
        self.configure(bg=self.bg_color)
        self.selected_profile = tk.StringVar()
        self.profile_names = {"内网": "内网", "外网": "外网", "专网": "专网"}
        self.network_configs = {}
        self.network_bindings = {}
        self.disable_others_var = tk.BooleanVar(value=True)
        
        # 配置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 定义字体
        self.header_font = font.Font(family="Microsoft YaHei UI", size=12, weight="bold")
        self.normal_font = font.Font(family="Microsoft YaHei UI", size=9)
        
        # 配置不同按钮样式
        self.style.configure("TButton", 
                            foreground=self.text_color, 
                            background=self.button_bg,
                            font=self.normal_font)
                            
        self.style.configure("Accent.TButton", 
                            foreground='white', 
                            background=self.accent_color,
                            font=self.normal_font)
                            
        self.style.configure("Profile.TButton", 
                            foreground=self.text_color, 
                            background=self.button_bg,
                            font=self.normal_font,
                            borderwidth=1)
                            
        self.style.configure("Selected.TButton", 
                            foreground='white', 
                            background=self.accent_color,
                            font=self.normal_font)
                            
        # 配置鼠标悬停效果
        self.style.map("Accent.TButton", 
                      background=[("active", self.accent_hover)])
        self.style.map("Selected.TButton", 
                      background=[("active", self.accent_hover)])
                      
        # 配置复选框样式                
        self.style.configure("TCheckbutton", 
                          background=self.bg_color,
                          font=self.normal_font)
        
        # 配置标签样式                          
        self.style.configure("TLabel", 
                          background=self.bg_color,
                          font=self.normal_font)
                          
        self.style.configure("Header.TLabel", 
                          background=self.bg_color,
                          font=self.header_font,
                          foreground=self.accent_color)
          # 配置下拉框样式
        self.style.configure("TCombobox", 
                          background=self.button_bg,
                          font=self.normal_font)        
        # 配置面板样式
        self.style.configure("TFrame", background=self.bg_color)
                          
        self.load_configurations()
        self.create_widgets()
        self.auto_select_active_profile()
        
        # 窗口创建完成后居中显示
        self.update_idletasks()  # 确保窗口尺寸已更新
        center_window(self)
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=15)
        
        # 标题和描述
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(header_frame, text="网络一键切换", style="Header.TLabel").pack(side='left')
        status_label = ttk.Label(header_frame, text="运行中...", foreground='green')
        status_label.pack(side='right')
        
        # 分隔线
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill='x', pady=5)
        
        # 网络配置选择区域
        config_frame = ttk.Frame(main_frame)
        config_frame.pack(fill='x', pady=10)
        
        ttk.Label(config_frame, text="选择网络配置:").pack(anchor='w')
        
        # 网络配置按钮容器
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        # 使用更大、更现代的按钮
        for i, key in enumerate(self.profile_names):
            b = ttk.Button(
                button_frame, 
                text=self.profile_names[key], 
                style="Profile.TButton",
                width=10,
                command=partial(self.select_profile, key)
            )
            b.grid(row=0, column=i, padx=5, pady=5, sticky='ew')
            button_frame.grid_columnconfigure(i, weight=1)
            setattr(self, f"btn_{key}", b)
        
        # 分隔线
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill='x', pady=10)
        
        # 操作按钮区
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill='x', pady=5)
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)
        
        # 第一行操作按钮
        first_row = ttk.Frame(action_frame)
        first_row.pack(fill='x', pady=5)
        
        ttk.Button(
            first_row, 
            text="配置当前网络", 
            command=self.open_config_window
        ).pack(side='left', padx=5, fill='x', expand=True)
        
        ttk.Button(
            first_row, 
            text="应用配置", 
            style="Accent.TButton", 
            command=self.apply_selected_config
        ).pack(side='right', padx=5, fill='x', expand=True)
        
        # 第二行操作按钮
        second_row = ttk.Frame(action_frame)
        second_row.pack(fill='x', pady=5)
        
        ttk.Button(
            second_row, 
            text="重命名配置",
            command=self.rename_profile
        ).pack(side='left', padx=5, fill='x', expand=True)
        
        ttk.Button(
            second_row, 
            text="所有网卡自动获取IP",
            command=self.set_dhcp_all
        ).pack(side='right', padx=5, fill='x', expand=True)
        
        # 底部选项区
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Checkbutton(
            bottom_frame, 
            text="应用配置时禁用其他网卡",
            variable=self.disable_others_var
        ).pack(side='left')
        
    def select_profile(self, name):
        self.selected_profile.set(name)
        for key in self.profile_names:
            btn = getattr(self, f"btn_{key}")
            btn.configure(style="Profile.TButton")
        getattr(self, f"btn_{name}").configure(style="Selected.TButton")
        
    # 重命名网络名称
    def rename_profile(self):
        name = self.selected_profile.get()
        if not name:
            messagebox.showwarning("提示", "请先选择一个网络")
            return
            
        # 使用自定义对话框而不是simpledialog
        dialog = RenameDialog(self, "重命名配置", self.profile_names[name])
        new_name = dialog.result
        
        if new_name:
            # 如果名称没有改变，则忽略操作
            if new_name == self.profile_names[name]:
                return
                
            # 检查是否与其他配置名称重复
            for key, value in self.profile_names.items():
                if key != name and value == new_name:
                    messagebox.showerror("错误", f"名称 '{new_name}' 已被使用")
                    return
                    
            # 应用新名称
            self.profile_names[name] = new_name
            getattr(self, f"btn_{name}").configure(text=new_name)
            
            # 保存更改到配置文件
            self.save_to_file()
            messagebox.showinfo("重命名成功", f"已将配置名称更改为 '{new_name}'")

    def open_config_window(self):
        name = self.selected_profile.get()
        if not name:
            messagebox.showwarning("提示", "请先选择一个网络")
            return
        ConfigWindow(self, self.profile_names[name], self.save_config, self.network_bindings)

    def save_config(self, name, config):
        self.network_configs[name] = config
        self.save_to_file()
        messagebox.showinfo("保存成功", f"已保存 {name} 配置")

    def apply_selected_config(self):
        name = self.selected_profile.get()
        config = self.network_configs.get(name)
        if not config:
            messagebox.showerror("错误", f"未找到 {name} 配置")
            return

        if self.disable_others_var.get():
            for profile, cfg in self.network_configs.items():
                if profile != name and cfg.get('interface'):
                    disable_interface(cfg['interface'])

        enable_interface(config['interface'])

        if config.get('dhcp'):
            set_dhcp(config['interface'])
        else:
            set_static_ip(config['interface'], config['ip'], config['mask'], config['gateway'], config['dns'])

        messagebox.showinfo("完成", f"已应用 {name} 配置")

    def set_dhcp_all(self):
        for iface in get_network_interfaces():
            enable_interface(iface)
            set_dhcp(iface)
        messagebox.showinfo("完成", "所有网卡已设置为自动获取IP")

    def save_to_file(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "configs": self.network_configs,
                    "bindings": self.network_bindings,
                    "profile_names": self.profile_names
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存配置文件: {e}")

    def load_configurations(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.network_configs = data.get("configs", {})
                    self.network_bindings = data.get("bindings", {})
                    self.profile_names = data.get("profile_names", self.profile_names)
            except Exception as e:
                messagebox.showwarning("读取配置失败", f"加载配置文件出错: {e}")
    
    def auto_select_active_profile(self):
        active_ifaces = get_active_interfaces()
        for profile, iface in self.network_bindings.items():
            if iface in active_ifaces:
                self.select_profile(profile)
                break
