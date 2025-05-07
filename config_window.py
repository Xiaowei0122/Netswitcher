# config_window.py - 配置窗口类
import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
from utils import get_network_interfaces, get_interface_ip, enable_interface, center_window

class ConfigWindow(tk.Toplevel):
    def __init__(self, parent, title, save_callback, binding):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title(f"配置 - {title}")
        
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
        
        # 其他属性
        self.save_callback = save_callback
        self.binding = binding
        self.network_name = title
        self.geometry("440x520")
          # 设置窗口样式
        self.configure(bg=self.bg_color)
        self.interface_var = tk.StringVar()
        self.use_dhcp_var = tk.BooleanVar(value=False)
        # 继承父窗口的字体
        self.header_font = parent.header_font
        self.normal_font = parent.normal_font
        
        self.create_form()
        
        # 窗口创建完成后居中显示
        self.update_idletasks()  # 确保窗口尺寸已更新
        center_window(self)
        
    def create_form(self):
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=15)
        
        # 标题部分
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(header_frame, text=f"配置 - {self.network_name}", 
                 font=self.header_font, foreground=self.accent_color).pack(anchor='w')
        
        # 网卡选择部分
        card_frame = ttk.LabelFrame(main_frame, text="网卡设置", padding=(10, 5))
        card_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(card_frame, text="选择网卡:").grid(row=0, column=0, sticky='w', pady=(5, 0))
        self.interface_list = ttk.Combobox(card_frame, textvariable=self.interface_var, state="readonly", width=30)
        self.interface_list.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        self.interface_list['values'] = get_network_interfaces()
        
        bind_frame = ttk.Frame(card_frame)
        bind_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        
        self.bound_label = ttk.Label(bind_frame, text="", foreground="blue")
        self.bound_label.pack(side='left')
        
        self.bind_btn = ttk.Button(bind_frame, text="绑定到此网卡", command=self.toggle_binding)
        self.bind_btn.pack(side='right')
        
        # IP设置部分
        ip_frame = ttk.LabelFrame(main_frame, text="IP设置", padding=(10, 5))
        ip_frame.pack(fill='x', padx=5, pady=(15, 5))
        
        # DHCP选项
        dhcp_frame = ttk.Frame(ip_frame)
        dhcp_frame.pack(fill='x', padx=5, pady=5)
        
        self.dhcp_checkbox = ttk.Checkbutton(
            dhcp_frame, 
            text="自动获取IP (DHCP)", 
            variable=self.use_dhcp_var, 
            command=self.toggle_fields
        )
        self.dhcp_checkbox.pack(anchor='w')
        
        # IP字段
        labels = ["IP地址", "子网掩码", "默认网关", "DNS (多个用逗号分隔)"]
        self.entries = []
        self.fields_frame = ttk.Frame(ip_frame)
        self.fields_frame.pack(fill='x', padx=5, pady=10)
        
        # 使用网格布局让字段更整齐
        for i, label in enumerate(labels):
            ttk.Label(self.fields_frame, text=label).grid(row=i, column=0, sticky='w', pady=(5, 0))
            entry = ttk.Entry(self.fields_frame)
            entry.grid(row=i, column=1, sticky='ew', padx=5, pady=5)
            self.entries.append(entry)
            self.fields_frame.grid_columnconfigure(1, weight=1)
        
        # 操作按钮区
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', padx=5, pady=15)
        
        ttk.Button(
            button_frame, 
            text="读取当前配置", 
            command=self.read_current_config
        ).pack(side='left', padx=5, fill='x', expand=True)
        
        ttk.Button(
            button_frame, 
            text="保存配置", 
            style="Accent.TButton",
            command=self.on_save
        ).pack(side='right', padx=5, fill='x', expand=True)

        self.load_binding()

    def load_binding(self):
        bound = self.binding.get(self.network_name)
        if bound:
            try:
                index = self.interface_list['values'].index(bound)
                self.interface_list.current(index)
            except ValueError:
                self.interface_list.current(0)
            self.bound_label.config(text=f"已绑定网卡: {bound}")
            self.bind_btn.config(text="解绑网卡")
        elif self.interface_list['values']:
            self.interface_list.current(0)
            self.bound_label.config(text="未绑定网卡")
            self.bind_btn.config(text="绑定到此网卡")
        self.toggle_fields()

    def toggle_binding(self):
        current = self.interface_var.get()
        if self.binding.get(self.network_name) == current:
            del self.binding[self.network_name]
            messagebox.showinfo("解绑成功", f"{self.network_name} 网卡解绑成功")
        else:
            self.binding[self.network_name] = current
            messagebox.showinfo("绑定成功", f"{self.network_name} 已绑定到网卡：{current}")
        self.load_binding()

    def toggle_fields(self):
        state = "disabled" if self.use_dhcp_var.get() else "normal"
        for entry in self.entries:
            entry.config(state=state)

    def read_current_config(self):
        iface = self.binding.get(self.network_name)
        if not iface:
            messagebox.showwarning("未绑定", "请先绑定一个网卡")
            return
        info = get_interface_ip(iface)
        is_dhcp = "DHCP 已启用: 是" in info
        self.use_dhcp_var.set(is_dhcp)
        self.toggle_fields()
        ip, mask, gateway = '', '', ''
        dns_list = []
        lines = info.splitlines()
        for i, line in enumerate(lines):
            if "IP 地址" in line and not ip:
                ip = line.split(":", 1)[-1].strip()
            elif "子网前缀" in line and not mask:
                if "掩码" in line:
                # 提取括号中的掩码
                    start = line.find("掩码")
                    if start != -1:
                        mask = line[start + 3:].replace(")", "").strip()
            elif "默认网关" in line:
                gateway = line.split(":", 1)[-1].strip()
            elif "DNS 服务器" in line:
            # 提取主行 DNS
                dns_line = line.split(":", 1)[-1]
                dns_list += re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', dns_line)
                # 提取后续 DNS 行
                j = i + 1
                while j < len(lines):
                    potential = lines[j].strip()
                    if potential == "":
                        break
                    matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', potential)
                    if matches:
                        dns_list.extend(matches)
                    else:
                        break
                    j += 1
        dns = ", ".join(dns_list)
        values = [ip, mask, gateway, dns]
        for entry, val in zip(self.entries, values):
            entry.config(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, val)
        self.toggle_fields()

    def on_save(self):
        iface = self.binding.get(self.network_name)
        if not iface:
            messagebox.showerror("错误", "请先绑定网卡")
            return

        config = {
            'interface': iface,
            'dhcp': self.use_dhcp_var.get()
        }

        if not config['dhcp']:
            values = [entry.get() for entry in self.entries]
            if not all(values):
                messagebox.showerror("错误", "所有字段都不能为空")
                return
            config.update({
                'ip': values[0],
                'mask': values[1],
                'gateway': values[2],
                'dns': values[3]
            })

        self.save_callback(self.network_name, config)
        self.destroy()
