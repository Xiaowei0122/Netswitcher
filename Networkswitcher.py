import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import ctypes
import json
import os
import re

CONFIG_FILE = "network_config.json"

# 检查管理员权限
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
    
# 返回当前活动网卡名称
def get_active_interfaces():
    result = subprocess.run("netsh interface ip show config", capture_output=True, text=True, shell=True)
    interfaces = []
    current_name = None
    for line in result.stdout.splitlines():
        if "配置接口" in line or "Configuration for interface" in line:
            current_name = line.split('"')[1]
        elif "IP 地址" in line and current_name:
            interfaces.append(current_name)
            current_name = None
    return interfaces

# 获取所有网卡名称
def get_network_interfaces():
    result = subprocess.run("netsh interface show interface", capture_output=True, text=True, shell=True)
    interfaces = []
    for line in result.stdout.splitlines():
        if "已连接" in line or "已断开" in line:
            parts = line.split()
            name = " ".join(parts[3:])
            interfaces.append(name)
    return interfaces

# 设置静态IP地址、子网掩码、网关和DNS
def set_static_ip(interface, ip, mask, gateway, dns):
    subprocess.run(f"netsh interface ip set address name=\"{interface}\" static {ip} {mask} {gateway}", shell=True)
    subprocess.run(f"netsh interface ip set dns name=\"{interface}\" source=static addr=none register=none", shell=True)
    dns_list = [d.strip() for d in dns.split(",") if d.strip()]
    for i, d in enumerate(dns_list):
        subprocess.run(f"netsh interface ip add dns name=\"{interface}\" addr={d} {'index=1' if i == 0 else ''}", shell=True)

# 设置为自动获取IP和DNS
def set_dhcp(interface):
    subprocess.run(f"netsh interface ip set address name=\"{interface}\" source=dhcp", shell=True)
    subprocess.run(f"netsh interface ip set dnsservers name=\"{interface}\" source=dhcp", shell=True)

# 启用网卡
def enable_interface(interface):
    subprocess.run(f"netsh interface set interface name=\"{interface}\" admin=enable", shell=True)

# 禁用网卡
def disable_interface(interface):
    subprocess.run(f"netsh interface set interface name=\"{interface}\" admin=disable", shell=True)

# 获取当前IP配置
def get_interface_ip(interface):
    result = subprocess.run(f"netsh interface ip show config name=\"{interface}\"", capture_output=True, text=True, shell=True)
    return result.stdout

class ConfigWindow(tk.Toplevel):
    def __init__(self, parent, title, save_callback, binding):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title(f"配置 - {title}")
        self.save_callback = save_callback
        self.binding = binding
        self.network_name = title
        self.geometry("400x500")
        self.configure(bg='#f0f0f0')
        self.interface_var = tk.StringVar()
        self.use_dhcp_var = tk.BooleanVar(value=False)
        self.create_form()

    def create_form(self):
        ttk.Label(self, text="选择网卡:").pack(pady=(10, 0))
        self.interface_list = ttk.Combobox(self, textvariable=self.interface_var, state="readonly")
        self.interface_list.pack(pady=5, fill='x', padx=10)
        self.interface_list['values'] = get_network_interfaces()

        self.bound_label = ttk.Label(self, text="")
        self.bound_label.pack()

        self.bind_btn = ttk.Button(self, text="绑定到此网卡", command=self.toggle_binding)
        self.bind_btn.pack(pady=(5, 10))

        self.dhcp_checkbox = ttk.Checkbutton(self, text="自动获取IP (DHCP)", variable=self.use_dhcp_var, command=self.toggle_fields)
        self.dhcp_checkbox.pack(pady=5)

        labels = ["IP地址", "子网掩码", "默认网关", "DNS"]
        self.entries = []
        self.fields_frame = ttk.Frame(self)
        self.fields_frame.pack(pady=5, fill='x', padx=10)

        for label in labels:
            ttk.Label(self.fields_frame, text=label).pack(anchor='w', pady=(5, 0))
            entry = ttk.Entry(self.fields_frame)
            entry.pack(fill='x')
            self.entries.append(entry)

        ttk.Button(self, text="读取当前配置", command=self.read_current_config).pack(pady=(10, 5))
        ttk.Button(self, text="保存配置", command=self.on_save).pack(pady=10)

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

class SimpleNetworkSwitcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("网络一键切换器")
        self.resizable(False,False)
        self.geometry("380x250")
        self.configure(bg='#ffffff')
        self.selected_profile = tk.StringVar()
        self.profile_names = {"内网": "内网", "外网": "外网", "专网": "专网"}
        self.network_configs = {}
        self.network_bindings = {}
        self.disable_others_var = tk.BooleanVar(value=True)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Accent.TButton", foreground="white", background="#0078D7")
        self.style.map("Accent.TButton", background=[("active", "#005A9E")])
        self.load_configurations()
        self.create_widgets()
        self.auto_select_active_profile()

    def create_widgets(self):
        ttk.Label(self, text="网络配置列表:", font=("Segoe UI", 11, "bold")).pack(pady=10)

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        for key in self.profile_names:
            b = ttk.Button(button_frame, text=self.profile_names[key], width=10, command=lambda n=key: self.select_profile(n))
            b.pack(side='left', padx=5)
            setattr(self, f"btn_{key}", b)

        rename_frame = ttk.Frame(self)
        rename_frame.pack(pady=5)
        ttk.Button(rename_frame, text="重命名配置名称", command=self.rename_profile).pack(side='left', padx=5)
        ttk.Button(rename_frame, text="所有网卡自动获取IP(DHCP)", command=self.set_dhcp_all).pack(side='left', padx=5)

        action_frame = ttk.Frame(self)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="配置当前网络", command=self.open_config_window).pack(side='left', padx=10)
        ttk.Button(action_frame, text="应用配置", style="Accent.TButton", command=self.apply_selected_config).pack(side='left', padx=10)

        ttk.Checkbutton(self, text="应用配置时禁用其他网卡", variable=self.disable_others_var).pack(pady=5)

    def select_profile(self, name):
        self.selected_profile.set(name)
        for key in self.profile_names:
            btn = getattr(self, f"btn_{key}")
            btn.configure(style="TButton")
        getattr(self, f"btn_{name}").configure(style="Accent.TButton")
# 重命名网络名称
    def rename_profile(self):
        name = self.selected_profile.get()
        if not name:
            messagebox.showwarning("提示", "请先选择一个网络")
            return
        new_name = simpledialog.askstring("重命名", f"请输入新的名称 (原: {self.profile_names[name]})")
        if new_name:
            self.profile_names[name] = new_name
            getattr(self, f"btn_{name}").configure(text=new_name)

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
            
if __name__ == "__main__":
    if not is_admin():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("权限错误", "请以管理员身份运行此程序")
        root.destroy()
    else:
        app = SimpleNetworkSwitcher()
        app.mainloop()
