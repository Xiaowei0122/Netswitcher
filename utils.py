# utils.py - 实用功能模块
import subprocess
import ctypes
import re

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

# 计算居中位置的坐标
def get_center_position(window, width, height):
    """
    计算窗口居中显示时的坐标
    :param window: tkinter窗口实例
    :param width: 窗口宽度
    :param height: 窗口高度
    :return: 窗口居中显示的位置坐标
    """
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    return x, y

# 使窗口在屏幕上居中显示（已创建的窗口）
def center_window(window):
    """
    使已创建的窗口在屏幕上居中显示
    :param window: tkinter窗口实例
    """
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x, y = get_center_position(window, width, height)
    window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
