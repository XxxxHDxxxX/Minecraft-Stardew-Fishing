import sys
import time
import threading
import cv2
import numpy as np
import pyautogui
from PIL import ImageGrab, Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox, Scale, HORIZONTAL, filedialog
import json
import os

class StardewFishingBot:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft Stardew Fishing 自动钓鱼助手")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 默认区域设置
        self.screen_width, self.screen_height = pyautogui.size()
        x = int(self.screen_width/2 - 150)
        y = int(self.screen_height/2 - 250)
        w = 300
        h = 500

        # 确保x和y不为负
        x = max(0, x)
        y = max(0, y)

        # 确保区域不超出屏幕边界
        if x + w > self.screen_width:
            w = self.screen_width - x
        if y + h > self.screen_height:
            h = self.screen_height - y

        self.game_region = (x, y, w, h)
        #self.game_region = (int(self.screen_width/2-150), int(self.screen_height/2-250), 300, 500)
        
        # 默认颜色设置
        self.fish_color_lower = np.array([50, 80, 80])
        self.fish_color_upper = np.array([100, 150, 150])
        self.green_bar_color_lower = np.array([40, 160, 40])
        self.green_bar_color_upper = np.array([100, 255, 100])
        self.blue_area_color_lower = np.array([160, 100, 40])
        self.blue_area_color_upper = np.array([240, 180, 100])
        
        # 控制参数
        self.position_threshold = 10
        self.max_click_delay = 0.15
        self.min_click_delay = 0.01
        self.cast_cooldown = 5
        
        # 状态变量
        self.running = False
        self.thread = None
        self.last_cast_time = 0
        self.preview_image = None
        self.detected_fish_pos = None
        self.detected_green_pos = None
        
        self.create_ui()
    
    def create_ui(self):
        # 创建标签页
        self.tab_control = ttk.Notebook(self.root)
        
        # 主控制标签页
        self.tab_main = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_main, text="主控制")
        
        # 区域设置标签页
        self.tab_region = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_region, text="区域设置")
        
        # 颜色设置标签页
        self.tab_color = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_color, text="颜色设置")
        
        # 高级设置标签页
        self.tab_advanced = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_advanced, text="高级设置")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # 设置各个标签页
        self.setup_main_tab()
        self.setup_region_tab()
        self.setup_color_tab()
        self.setup_advanced_tab()
    
    def setup_main_tab(self):
        # 左侧控制面板
        
        control_frame = ttk.LabelFrame(self.tab_main, text="控制")
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nw")
        
        # 开始/停止按钮
        self.start_button = ttk.Button(control_frame, text="开始", command=self.toggle_bot)
        self.start_button.grid(row=0, column=0, padx=10, pady=10)
        
        # 手动投掷鱼竿按钮
        cast_button = ttk.Button(control_frame, text="投掷鱼竿", command=self.manual_cast)
        cast_button.grid(row=1, column=0, padx=10, pady=10)
        
        # 自动投掷鱼竿选项
        self.auto_cast_var = tk.BooleanVar(value=True)
        auto_cast_check = ttk.Checkbutton(control_frame, text="自动投掷鱼竿", variable=self.auto_cast_var)
        auto_cast_check.grid(row=2, column=0, padx=10, pady=10)
        
        # 状态信息
        status_frame = ttk.LabelFrame(control_frame, text="状态")
        status_frame.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        
        self.status_label = ttk.Label(status_frame, text="已停止")
        self.status_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.fish_pos_label = ttk.Label(status_frame, text="鱼位置: 未检测")
        self.fish_pos_label.grid(row=1, column=0, padx=10, pady=2, sticky="w")
        
        self.green_pos_label = ttk.Label(status_frame, text="绿色条位置: 未检测")
        self.green_pos_label.grid(row=2, column=0, padx=10, pady=2, sticky="w")
        
        self.distance_label = ttk.Label(status_frame, text="位置差: 0")
        self.distance_label.grid(row=3, column=0, padx=10, pady=2, sticky="w")
        
        # 右侧预览
        preview_frame = ttk.LabelFrame(self.tab_main, text="预览")
        preview_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ne")
        
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.grid(row=0, column=0, padx=10, pady=10)
        
        # 日志区域
        log_frame = ttk.LabelFrame(self.tab_main, text="日志")
        log_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        self.log_text = tk.Text(log_frame, height=10, width=70)
        self.log_text.grid(row=0, column=0, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 初始预览图像
        self.update_preview()
    
    def setup_region_tab(self):
        region_frame = ttk.Frame(self.tab_region)
        region_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ttk.Label(region_frame, text="设置检测区域 (x, y, 宽, 高)").grid(row=0, column=0, columnspan=4, pady=10)
        
        ttk.Label(region_frame, text="X:").grid(row=1, column=0, padx=5, pady=5)
        self.region_x_var = tk.IntVar(value=self.game_region[0])
        ttk.Entry(region_frame, textvariable=self.region_x_var, width=6).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(region_frame, text="Y:").grid(row=1, column=2, padx=5, pady=5)
        self.region_y_var = tk.IntVar(value=self.game_region[1])
        ttk.Entry(region_frame, textvariable=self.region_y_var, width=6).grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Label(region_frame, text="宽:").grid(row=2, column=0, padx=5, pady=5)
        self.region_w_var = tk.IntVar(value=self.game_region[2])
        ttk.Entry(region_frame, textvariable=self.region_w_var, width=6).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(region_frame, text="高:").grid(row=2, column=2, padx=5, pady=5)
        self.region_h_var = tk.IntVar(value=self.game_region[3])
        ttk.Entry(region_frame, textvariable=self.region_h_var, width=6).grid(row=2, column=3, padx=5, pady=5)
        
        # 自动检测区域按钮
        detect_button = ttk.Button(region_frame, text="自动检测区域", command=self.auto_detect_region)
        detect_button.grid(row=3, column=0, columnspan=2, padx=5, pady=20)
        
        # 应用区域按钮
        apply_button = ttk.Button(region_frame, text="应用区域设置", command=self.apply_region)
        apply_button.grid(row=3, column=2, columnspan=2, padx=5, pady=20)
        
        # 当前屏幕大小信息
        ttk.Label(region_frame, text=f"屏幕分辨率: {self.screen_width}x{self.screen_height}").grid(row=4, column=0, columnspan=4, padx=5, pady=5)
        
        # 区域预览
        preview_frame = ttk.LabelFrame(region_frame, text="区域预览")
        preview_frame.grid(row=5, column=0, columnspan=4, padx=10, pady=10)
        
        self.region_preview_label = ttk.Label(preview_frame)
        self.region_preview_label.pack(padx=10, pady=10)
        
        # 更新区域预览
        self.update_region_preview()
    
    def setup_color_tab(self):
        # 鱼颜色设置
        fish_frame = ttk.LabelFrame(self.tab_color, text="鱼颜色设置 (BGR)")
        fish_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nw")
        
        ttk.Label(fish_frame, text="下限:").grid(row=0, column=0, pady=5)
        
        ttk.Label(fish_frame, text="B:").grid(row=1, column=0, padx=5, pady=5)
        self.fish_b_lower = tk.IntVar(value=self.fish_color_lower[0])
        ttk.Entry(fish_frame, textvariable=self.fish_b_lower, width=4).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(fish_frame, text="G:").grid(row=2, column=0, padx=5, pady=5)
        self.fish_g_lower = tk.IntVar(value=self.fish_color_lower[1])
        ttk.Entry(fish_frame, textvariable=self.fish_g_lower, width=4).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(fish_frame, text="R:").grid(row=3, column=0, padx=5, pady=5)
        self.fish_r_lower = tk.IntVar(value=self.fish_color_lower[2])
        ttk.Entry(fish_frame, textvariable=self.fish_r_lower, width=4).grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(fish_frame, text="上限:").grid(row=0, column=2, pady=5)
        
        ttk.Label(fish_frame, text="B:").grid(row=1, column=2, padx=5, pady=5)
        self.fish_b_upper = tk.IntVar(value=self.fish_color_upper[0])
        ttk.Entry(fish_frame, textvariable=self.fish_b_upper, width=4).grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Label(fish_frame, text="G:").grid(row=2, column=2, padx=5, pady=5)
        self.fish_g_upper = tk.IntVar(value=self.fish_color_upper[1])
        ttk.Entry(fish_frame, textvariable=self.fish_g_upper, width=4).grid(row=2, column=3, padx=5, pady=5)
        
        ttk.Label(fish_frame, text="R:").grid(row=3, column=2, padx=5, pady=5)
        self.fish_r_upper = tk.IntVar(value=self.fish_color_upper[2])
        ttk.Entry(fish_frame, textvariable=self.fish_r_upper, width=4).grid(row=3, column=3, padx=5, pady=5)
        
        # 绿色条颜色设置
        green_frame = ttk.LabelFrame(self.tab_color, text="绿色条颜色设置 (BGR)")
        green_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nw")
        
        ttk.Label(green_frame, text="下限:").grid(row=0, column=0, pady=5)
        
        ttk.Label(green_frame, text="B:").grid(row=1, column=0, padx=5, pady=5)
        self.green_b_lower = tk.IntVar(value=self.green_bar_color_lower[0])
        ttk.Entry(green_frame, textvariable=self.green_b_lower, width=4).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(green_frame, text="G:").grid(row=2, column=0, padx=5, pady=5)
        self.green_g_lower = tk.IntVar(value=self.green_bar_color_lower[1])
        ttk.Entry(green_frame, textvariable=self.green_g_lower, width=4).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(green_frame, text="R:").grid(row=3, column=0, padx=5, pady=5)
        self.green_r_lower = tk.IntVar(value=self.green_bar_color_lower[2])
        ttk.Entry(green_frame, textvariable=self.green_r_lower, width=4).grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(green_frame, text="上限:").grid(row=0, column=2, pady=5)
        
        ttk.Label(green_frame, text="B:").grid(row=1, column=2, padx=5, pady=5)
        self.green_b_upper = tk.IntVar(value=self.green_bar_color_upper[0])
        ttk.Entry(green_frame, textvariable=self.green_b_upper, width=4).grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Label(green_frame, text="G:").grid(row=2, column=2, padx=5, pady=5)
        self.green_g_upper = tk.IntVar(value=self.green_bar_color_upper[1])
        ttk.Entry(green_frame, textvariable=self.green_g_upper, width=4).grid(row=2, column=3, padx=5, pady=5)
        
        ttk.Label(green_frame, text="R:").grid(row=3, column=2, padx=5, pady=5)
        self.green_r_upper = tk.IntVar(value=self.green_bar_color_upper[2])
        ttk.Entry(green_frame, textvariable=self.green_r_upper, width=4).grid(row=3, column=3, padx=5, pady=5)
        
        # 蓝色区域颜色设置
        blue_frame = ttk.LabelFrame(self.tab_color, text="蓝色区域颜色设置 (BGR)")
        blue_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nw")
        
        ttk.Label(blue_frame, text="下限:").grid(row=0, column=0, pady=5)
        
        ttk.Label(blue_frame, text="B:").grid(row=1, column=0, padx=5, pady=5)
        self.blue_b_lower = tk.IntVar(value=self.blue_area_color_lower[0])
        ttk.Entry(blue_frame, textvariable=self.blue_b_lower, width=4).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(blue_frame, text="G:").grid(row=2, column=0, padx=5, pady=5)
        self.blue_g_lower = tk.IntVar(value=self.blue_area_color_lower[1])
        ttk.Entry(blue_frame, textvariable=self.blue_g_lower, width=4).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(blue_frame, text="R:").grid(row=3, column=0, padx=5, pady=5)
        self.blue_r_lower = tk.IntVar(value=self.blue_area_color_lower[2])
        ttk.Entry(blue_frame, textvariable=self.blue_r_lower, width=4).grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(blue_frame, text="上限:").grid(row=0, column=2, pady=5)
        
        ttk.Label(blue_frame, text="B:").grid(row=1, column=2, padx=5, pady=5)
        self.blue_b_upper = tk.IntVar(value=self.blue_area_color_upper[0])
        ttk.Entry(blue_frame, textvariable=self.blue_b_upper, width=4).grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Label(blue_frame, text="G:").grid(row=2, column=2, padx=5, pady=5)
        self.blue_g_upper = tk.IntVar(value=self.blue_area_color_upper[1])
        ttk.Entry(blue_frame, textvariable=self.blue_g_upper, width=4).grid(row=2, column=3, padx=5, pady=5)
        
        ttk.Label(blue_frame, text="R:").grid(row=3, column=2, padx=5, pady=5)
        self.blue_r_upper = tk.IntVar(value=self.blue_area_color_upper[2])
        ttk.Entry(blue_frame, textvariable=self.blue_r_upper, width=4).grid(row=3, column=3, padx=5, pady=5)
        
        # 颜色拾取工具
        picker_frame = ttk.LabelFrame(self.tab_color, text="颜色拾取工具")
        picker_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nw")
        
        ttk.Label(picker_frame, text="将鼠标放在屏幕上的颜色上\n按下按钮获取颜色值").grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        
        ttk.Button(picker_frame, text="获取鱼颜色", command=lambda: self.pick_color("fish")).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(picker_frame, text="获取绿条颜色", command=lambda: self.pick_color("green")).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(picker_frame, text="获取蓝区颜色", command=lambda: self.pick_color("blue")).grid(row=2, column=0, padx=5, pady=5)
        
        # 应用颜色设置按钮
        apply_button = ttk.Button(self.tab_color, text="应用颜色设置", command=self.apply_colors)
        apply_button.grid(row=2, column=0, columnspan=2, padx=10, pady=20)
        
        # 颜色预览
        preview_frame = ttk.LabelFrame(self.tab_color, text="颜色检测预览")
        preview_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10)
        
        self.color_preview_label = ttk.Label(preview_frame)
        self.color_preview_label.pack(padx=10, pady=10)
        
        # 定期更新颜色预览
        self.update_color_preview()
    
    def setup_advanced_tab(self):
        advanced_frame = ttk.Frame(self.tab_advanced)
        advanced_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 位置阈值设置
        ttk.Label(advanced_frame, text="位置阈值:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.threshold_var = tk.IntVar(value=self.position_threshold)
        threshold_scale = Scale(advanced_frame, from_=1, to=50, orient=HORIZONTAL, 
                                variable=self.threshold_var, length=300)
        threshold_scale.grid(row=0, column=1, padx=5, pady=5)
        
        # 最大点击延迟
        ttk.Label(advanced_frame, text="最大点击延迟 (秒):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.max_delay_var = tk.DoubleVar(value=self.max_click_delay)
        max_delay_scale = Scale(advanced_frame, from_=0.01, to=0.5, orient=HORIZONTAL, 
                                resolution=0.01, variable=self.max_delay_var, length=300)
        max_delay_scale.grid(row=1, column=1, padx=5, pady=5)
        
        # 最小点击延迟
        ttk.Label(advanced_frame, text="最小点击延迟 (秒):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.min_delay_var = tk.DoubleVar(value=self.min_click_delay)
        min_delay_scale = Scale(advanced_frame, from_=0.001, to=0.1, orient=HORIZONTAL, 
                                resolution=0.001, variable=self.min_delay_var, length=300)
        min_delay_scale.grid(row=2, column=1, padx=5, pady=5)
        
        # 投掷鱼竿冷却时间
        ttk.Label(advanced_frame, text="投掷鱼竿冷却时间 (秒):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.cast_cooldown_var = tk.DoubleVar(value=self.cast_cooldown)
        cast_cooldown_scale = Scale(advanced_frame, from_=1, to=15, orient=HORIZONTAL, 
                                   resolution=0.5, variable=self.cast_cooldown_var, length=300)
        cast_cooldown_scale.grid(row=3, column=1, padx=5, pady=5)
        
        # 应用高级设置按钮
        apply_button = ttk.Button(advanced_frame, text="应用高级设置", command=self.apply_advanced)
        apply_button.grid(row=4, column=0, columnspan=2, padx=10, pady=20)
        
        # 高级调试选项
        debug_frame = ttk.LabelFrame(advanced_frame, text="调试选项")
        debug_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        self.show_masks_var = tk.BooleanVar(value=True)
        show_masks_check = ttk.Checkbutton(debug_frame, text="在预览中显示颜色掩码", variable=self.show_masks_var)
        show_masks_check.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.debug_mode_var = tk.BooleanVar(value=False)
        debug_mode_check = ttk.Checkbutton(debug_frame, text="启用调试模式 (详细日志)", variable=self.debug_mode_var)
        debug_mode_check.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        # 保存和加载配置
        config_frame = ttk.LabelFrame(advanced_frame, text="配置")
        config_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        ttk.Button(config_frame, text="保存配置", command=self.save_config).grid(row=0, column=0, padx=10, pady=5)
        ttk.Button(config_frame, text="加载配置", command=self.load_config).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(config_frame, text="重置为默认", command=self.reset_config).grid(row=0, column=2, padx=10, pady=5)
    
    def toggle_bot(self):
        if self.running:
            self.running = False
            self.start_button.config(text="开始")
            self.status_label.config(text="已停止")
            self.log("自动钓鱼已停止")
        else:
            self.running = True
            self.start_button.config(text="停止")
            self.status_label.config(text="运行中")
            self.log("自动钓鱼已启动")
            
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self.run_bot)
                self.thread.daemon = True
                self.thread.start()
    
    def run_bot(self):
        fishing_active = False
        last_cast_time = 0
        
        while self.running:
            try:
                # 捕获屏幕
                screen = self.capture_screen(self.game_region)
                
                # 检测是否激活了钓鱼界面
                if self.detect_fishing_ui(screen):
                    if not fishing_active:
                        self.log("检测到钓鱼界面！开始自动控制...")
                        fishing_active = True
                    
                    # 获取鱼和绿色条的位置
                    self.detected_fish_pos = self.detect_element_position(screen, self.fish_color_lower, self.fish_color_upper)
                    self.detected_green_pos = self.detect_element_position(screen, self.green_bar_color_lower, self.green_bar_color_upper)
                    
                    if self.detected_fish_pos is not None and self.detected_green_pos is not None:
                        # 更新状态标签
                        self.update_status_labels()
                        
                        # 计算位置差
                        distance = self.detected_fish_pos - self.detected_green_pos
                        
                        # 位置控制策略
                        if distance > self.position_threshold:  # 鱼在绿色条下方
                            # 距离越大，点击频率越高
                            click_delay = max(self.min_click_delay, self.max_click_delay - (abs(distance) / 200))
                            pyautogui.click()
                            if self.debug_mode_var.get():
                                self.log(f"点击 (距离: {distance}, 延迟: {click_delay:.3f})")
                            time.sleep(click_delay)
                        elif distance < -self.position_threshold:  # 鱼在绿色条上方
                            # 不点击，让绿色条自然下落
                            if self.debug_mode_var.get():
                                self.log(f"等待下落 (距离: {distance})")
                            time.sleep(0.05)
                        else:  # 位置接近，轻点维持
                            time.sleep(0.08)
                            if distance > 0:  # 微调，如果鱼稍微在下方，轻点一下
                                pyautogui.click()
                                if self.debug_mode_var.get():
                                    self.log(f"微调点击 (距离: {distance})")
                else:
                    if fishing_active:
                        self.log("钓鱼界面消失，等待下一次钓鱼...")
                        fishing_active = False
                        self.detected_fish_pos = None
                        self.detected_green_pos = None
                        self.update_status_labels()
                    
                    # 如果启用了自动投掷，且上次投掷后已经过了足够长时间，且当前没有钓鱼界面，重新投掷鱼竿
                    current_time = time.time()
                    if self.auto_cast_var.get() and current_time - last_cast_time > self.cast_cooldown:
                        self.log("尝试投掷鱼竿...")
                        pyautogui.rightClick()
                        last_cast_time = current_time
                        time.sleep(1.5)  # 等待投掷动画
                
                # 更新预览
                self.update_preview()
                current_time = time.time()
                if self.auto_cast_var.get() and current_time - last_cast_time > self.cast_cooldown:
                    self.log("尝试投掷鱼竿...")
                    pyautogui.rightClick()
                    last_cast_time = current_time
                    time.sleep(1.5)  # 等待投掷动画
                
                # 更新预览
                self.update_preview()
                
            except Exception as e:
                self.log(f"运行时错误: {str(e)}")
                time.sleep(0.5)
        
        self.log("自动钓鱼线程已停止")

    def capture_screen(self, region=None):
        """捕获指定区域的屏幕"""
        if region:
            x, y, w, h = region
            # 确保宽度和高度是正值
            w = max(1, w)
            h = max(1, h)
            # 确保区域在屏幕范围内
            x = max(0, min(x, self.screen_width - w))
            y = max(0, min(y, self.screen_height - h))
            screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        else:
            screenshot = ImageGrab.grab()
        
        # 转换为OpenCV格式
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def detect_fishing_ui(self, screen):
        """检测屏幕上是否有钓鱼界面"""
        # 检测蓝色区域作为钓鱼界面指示器
        blue_mask = cv2.inRange(screen, self.blue_area_color_lower, self.blue_area_color_upper)
        blue_pixels = cv2.countNonZero(blue_mask)
        
        # 如果蓝色像素超过一定阈值，认为钓鱼界面已显示
        return blue_pixels > 200
    
    def detect_element_position(self, screen, color_lower, color_upper):
        """检测指定颜色元素在屏幕上的位置，返回Y坐标"""
        mask = cv2.inRange(screen, color_lower, color_upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # 找到最大的轮廓
            max_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(max_contour) > 50:  # 面积阈值，过滤噪点
                # 计算轮廓的中心点
                M = cv2.moments(max_contour)
                if M["m00"] != 0:
                    cy = int(M["m01"] / M["m00"])
                    return cy
        
        return None
    
    def update_preview(self, screen=None):
        """更新预览图像"""
        if screen is None:
            screen = self.capture_screen(self.game_region)
        
        # 创建预览图像
        preview = screen.copy()
        
        # 如果启用了掩码显示
        if self.show_masks_var.get():
            # 显示鱼的掩码
            fish_mask = cv2.inRange(screen, self.fish_color_lower, self.fish_color_upper)
            # 用红色标记鱼的区域
            preview[fish_mask > 0] = [0, 0, 255]  # 红色(BGR)
            
            # 显示绿色条的掩码
            green_mask = cv2.inRange(screen, self.green_bar_color_lower, self.green_bar_color_upper)
            # 用绿色标记绿色条的区域
            preview[green_mask > 0] = [0, 255, 0]  # 绿色(BGR)
        
        # 绘制鱼和绿色条的位置指示线
        if self.detected_fish_pos is not None:
            cv2.line(preview, (0, self.detected_fish_pos), (preview.shape[1], self.detected_fish_pos), (0, 255, 255), 1)
            
        if self.detected_green_pos is not None:
            cv2.line(preview, (0, self.detected_green_pos), (preview.shape[1], self.detected_green_pos), (0, 255, 0), 1)
        
        # 将OpenCV图像转换为PIL格式
        preview_image = Image.fromarray(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB))
        
        # 调整大小以适应UI
        preview_width = 300
        ratio = preview_width / preview_image.width
        preview_height = int(preview_image.height * ratio)
        preview_image = preview_image.resize((preview_width, preview_height), Image.LANCZOS)
        
        # 转换为Tkinter格式
        self.preview_image = ImageTk.PhotoImage(preview_image)
        
        # 更新预览标签
        self.preview_label.config(image=self.preview_image)
        
        # 安排下一次更新
        self.root.after(200, self.update_preview)
    
    def update_region_preview(self):
        """更新区域预览"""
        try:
            # 更新区域值
            x = self.region_x_var.get()
            y = self.region_y_var.get()
            width = self.region_w_var.get()
            height = self.region_h_var.get()
            
            # 捕获当前区域的屏幕
            screen = self.capture_screen((x, y, width, height))
            
            # 创建预览图像
            preview_image = Image.fromarray(cv2.cvtColor(screen, cv2.COLOR_BGR2RGB))
            
            # 调整大小以适应UI
            preview_width = 300
            ratio = preview_width / preview_image.width
            preview_height = int(preview_image.height * ratio)
            preview_image = preview_image.resize((preview_width, preview_height), Image.LANCZOS)
            
            # 转换为Tkinter格式
            self.region_preview_image = ImageTk.PhotoImage(preview_image)
            
            # 更新预览标签
            self.region_preview_label.config(image=self.region_preview_image)
        except Exception as e:
            self.log(f"更新区域预览出错: {str(e)}")
        
        # 安排下一次更新
        self.root.after(1000, self.update_region_preview)
    
    def update_color_preview(self):
        """更新颜色预览"""
        try:
            # 捕获当前区域的屏幕
            screen = self.capture_screen(self.game_region)
            
            # 创建预览图像
            preview = screen.copy()
            
            # 创建鱼的掩码
            fish_lower = np.array([self.fish_b_lower.get(), self.fish_g_lower.get(), self.fish_r_lower.get()])
            fish_upper = np.array([self.fish_b_upper.get(), self.fish_g_upper.get(), self.fish_r_upper.get()])
            fish_mask = cv2.inRange(screen, fish_lower, fish_upper)
            
            # 创建绿色条的掩码
            green_lower = np.array([self.green_b_lower.get(), self.green_g_lower.get(), self.green_r_lower.get()])
            green_upper = np.array([self.green_b_upper.get(), self.green_g_upper.get(), self.green_r_upper.get()])
            green_mask = cv2.inRange(screen, green_lower, green_upper)
            
            # 创建蓝色区域的掩码
            blue_lower = np.array([self.blue_b_lower.get(), self.blue_g_lower.get(), self.blue_r_lower.get()])
            blue_upper = np.array([self.blue_b_upper.get(), self.blue_g_upper.get(), self.blue_r_upper.get()])
            blue_mask = cv2.inRange(screen, blue_lower, blue_upper)
            
            # 用红色标记鱼的区域
            preview[fish_mask > 0] = [0, 0, 255]  # 红色(BGR)
            
            # 用绿色标记绿色条的区域
            preview[green_mask > 0] = [0, 255, 0]  # 绿色(BGR)
            
            # 用蓝色标记钓鱼界面区域
            preview[blue_mask > 0] = [255, 0, 0]  # 蓝色(BGR)
            
            # 将OpenCV图像转换为PIL格式
            preview_image = Image.fromarray(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB))
            
            # 调整大小以适应UI
            preview_width = 300
            ratio = preview_width / preview_image.width
            preview_height = int(preview_image.height * ratio)
            preview_image = preview_image.resize((preview_width, preview_height), Image.LANCZOS)
            
            # 转换为Tkinter格式
            self.color_preview_image = ImageTk.PhotoImage(preview_image)
            
            # 更新预览标签
            self.color_preview_label.config(image=self.color_preview_image)
        except Exception as e:
            self.log(f"更新颜色预览出错: {str(e)}")
        
        # 安排下一次更新
        self.root.after(500, self.update_color_preview)
    
    def update_status_labels(self):
        """更新状态标签"""
        if self.detected_fish_pos is not None:
            self.fish_pos_label.config(text=f"鱼位置: {self.detected_fish_pos}")
        else:
            self.fish_pos_label.config(text="鱼位置: 未检测")
        
        if self.detected_green_pos is not None:
            self.green_pos_label.config(text=f"绿色条位置: {self.detected_green_pos}")
        else:
            self.green_pos_label.config(text="绿色条位置: 未检测")
        
        if self.detected_fish_pos is not None and self.detected_green_pos is not None:
            distance = self.detected_fish_pos - self.detected_green_pos
            self.distance_label.config(text=f"位置差: {distance}")
        else:
            self.distance_label.config(text="位置差: 0")
    
    def log(self, message):
        """在日志框中添加消息"""
        current_time = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{current_time}] {message}\n")
        self.log_text.see(tk.END)  # 滚动到最新日志
    
    def auto_detect_region(self):
        """自动检测钓鱼界面区域"""
        self.log("请将游戏窗口切换到钓鱼界面，3秒后开始检测...")
        self.root.after(3000, self._perform_region_detection)
    
    def _perform_region_detection(self):
        """执行区域检测"""
        try:
            # 捕获全屏
            screen = self.capture_screen()
            
            # 检测蓝色区域（钓鱼界面特征）
            blue_mask = cv2.inRange(screen, self.blue_area_color_lower, self.blue_area_color_upper)
            contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # 找到最大的连通区域
                max_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(max_contour) > 1000:  # 面积阈值
                    # 获取边界框
                    x, y, w, h = cv2.boundingRect(max_contour)
                    
                    # 扩大区域以包含整个钓鱼界面
                    x = max(0, x - 50)
                    y = max(0, y - 50)
                    w = min(self.screen_width - x, w + 100)
                    h = min(self.screen_height - y, h + 100)
                    
                    # 更新区域变量
                    self.region_x_var.set(x)
                    self.region_y_var.set(y)
                    self.region_w_var.set(w)
                    self.region_h_var.set(h)
                    
                    self.log(f"检测到钓鱼界面区域: x={x}, y={y}, width={w}, height={h}")
                    return
            
            self.log("未能自动检测到钓鱼界面，请尝试手动设置或确保钓鱼界面已显示")
        except Exception as e:
            self.log(f"自动检测区域出错: {str(e)}")
    
    def apply_region(self):
        """应用区域设置"""
        try:
            x = self.region_x_var.get()
            y = self.region_y_var.get()
            w = self.region_w_var.get()
            h = self.region_h_var.get()
            
            # 边界检查
            if x < 0 or y < 0 or w <= 0 or h <= 0 or x+w > self.screen_width or y+h > self.screen_height:
                self.log("无效的区域设置，请确保区域在屏幕范围内且宽高为正值")
                return
            
            self.game_region = (x, y, w, h)
            self.log(f"已应用区域设置: x={x}, y={y}, width={w}, height={h}")
        except Exception as e:
            self.log(f"应用区域设置出错: {str(e)}")
    
    def apply_colors(self):
        """应用颜色设置"""
        try:
            # 更新鱼颜色
            self.fish_color_lower = np.array([self.fish_b_lower.get(), self.fish_g_lower.get(), self.fish_r_lower.get()])
            self.fish_color_upper = np.array([self.fish_b_upper.get(), self.fish_g_upper.get(), self.fish_r_upper.get()])
            
            # 更新绿色条颜色
            self.green_bar_color_lower = np.array([self.green_b_lower.get(), self.green_g_lower.get(), self.green_r_lower.get()])
            self.green_bar_color_upper = np.array([self.green_b_upper.get(), self.green_g_upper.get(), self.green_r_upper.get()])
            
            # 更新蓝色区域颜色
            self.blue_area_color_lower = np.array([self.blue_b_lower.get(), self.blue_g_lower.get(), self.blue_r_lower.get()])
            self.blue_area_color_upper = np.array([self.blue_b_upper.get(), self.blue_g_upper.get(), self.blue_r_upper.get()])
            
            self.log("颜色设置已应用")
        except Exception as e:
            self.log(f"应用颜色设置出错: {str(e)}")
    
    def apply_advanced(self):
        """应用高级设置"""
        try:
            self.position_threshold = self.threshold_var.get()
            self.max_click_delay = self.max_delay_var.get()
            self.min_click_delay = self.min_delay_var.get()
            self.cast_cooldown = self.cast_cooldown_var.get()
            
            self.log(f"已应用高级设置: 位置阈值={self.position_threshold}, 最大延迟={self.max_click_delay}, 最小延迟={self.min_click_delay}, 投掷冷却={self.cast_cooldown}")
        except Exception as e:
            self.log(f"应用高级设置出错: {str(e)}")
    
    def pick_color(self, target_type):
        """拾取鼠标位置的颜色"""
        self.log(f"3秒后获取鼠标位置的颜色值...")
        self.root.after(3000, lambda: self._perform_color_pick(target_type))
    
    def _perform_color_pick(self, target_type):
        """执行颜色拾取"""
        try:
            # 获取鼠标位置
            x, y = pyautogui.position()
            
            # 捕获屏幕
            screen = self.capture_screen()
            
            # 获取颜色值 (BGR)
            color = screen[y, x]
            b, g, r = color
            
            self.log(f"拾取颜色: B={b}, G={g}, R={r}")
            
            # 设置颜色范围（上下各浮动20）
            lower = np.array([max(0, b-20), max(0, g-20), max(0, r-20)])
            upper = np.array([min(255, b+20), min(255, g+20), min(255, r+20)])
            
            # 根据目标类型更新对应的颜色变量
            if target_type == "fish":
                self.fish_b_lower.set(lower[0])
                self.fish_g_lower.set(lower[1])
                self.fish_r_lower.set(lower[2])
                self.fish_b_upper.set(upper[0])
                self.fish_g_upper.set(upper[1])
                self.fish_r_upper.set(upper[2])
                self.log("已更新鱼颜色设置")
            elif target_type == "green":
                self.green_b_lower.set(lower[0])
                self.green_g_lower.set(lower[1])
                self.green_r_lower.set(lower[2])
                self.green_b_upper.set(upper[0])
                self.green_g_upper.set(upper[1])
                self.green_r_upper.set(upper[2])
                self.log("已更新绿条颜色设置")
            elif target_type == "blue":
                self.blue_b_lower.set(lower[0])
                self.blue_g_lower.set(lower[1])
                self.blue_r_lower.set(lower[2])
                self.blue_b_upper.set(upper[0])
                self.blue_g_upper.set(upper[1])
                self.blue_r_upper.set(upper[2])
                self.log("已更新蓝区颜色设置")
        except Exception as e:
            self.log(f"拾取颜色出错: {str(e)}")
    
    def manual_cast(self):
        """手动投掷鱼竿"""
        pyautogui.rightClick()
        self.last_cast_time = time.time()
        self.log("手动投掷鱼竿")
    
    def save_config(self):
        """保存配置到文件"""
        try:
            config = {
                "game_region": self.game_region,
                "fish_color_lower": self.fish_color_lower.tolist(),
                "fish_color_upper": self.fish_color_upper.tolist(),
                "green_bar_color_lower": self.green_bar_color_lower.tolist(),
                "green_bar_color_upper": self.green_bar_color_upper.tolist(),
                "blue_area_color_lower": self.blue_area_color_lower.tolist(),
                "blue_area_color_upper": self.blue_area_color_upper.tolist(),
                "position_threshold": self.position_threshold,
                "max_click_delay": self.max_click_delay,
                "min_click_delay": self.min_click_delay,
                "cast_cooldown": self.cast_cooldown
            }
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
                title="保存配置"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                self.log(f"配置已保存到: {file_path}")
        except Exception as e:
            self.log(f"保存配置出错: {str(e)}")
    
    def load_config(self):
        """从文件加载配置"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
                title="加载配置"
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新游戏区域
                self.game_region = tuple(config["game_region"])
                self.region_x_var.set(self.game_region[0])
                self.region_y_var.set(self.game_region[1])
                self.region_w_var.set(self.game_region[2])
                self.region_h_var.set(self.game_region[3])
                
                # 更新颜色设置
                self.fish_color_lower = np.array(config["fish_color_lower"])
                self.fish_color_upper = np.array(config["fish_color_upper"])
                self.green_bar_color_lower = np.array(config["green_bar_color_lower"])
                self.green_bar_color_upper = np.array(config["green_bar_color_upper"])
                self.blue_area_color_lower = np.array(config["blue_area_color_lower"])
                self.blue_area_color_upper = np.array(config["blue_area_color_upper"])
                
                # 更新颜色输入框
                self.fish_b_lower.set(self.fish_color_lower[0])
                self.fish_g_lower.set(self.fish_color_lower[1])
                self.fish_r_lower.set(self.fish_color_lower[2])
                self.fish_b_upper.set(self.fish_color_upper[0])
                self.fish_g_upper.set(self.fish_color_upper[1])
                self.fish_r_upper.set(self.fish_color_upper[2])
                
                self.green_b_lower.set(self.green_bar_color_lower[0])
                self.green_g_lower.set(self.green_bar_color_lower[1])
                self.green_r_lower.set(self.green_bar_color_lower[2])
                self.green_b_upper.set(self.green_bar_color_upper[0])
                self.green_g_upper.set(self.green_bar_color_upper[1])
                self.green_r_upper.set(self.green_bar_color_upper[2])
                
                self.blue_b_lower.set(self.blue_area_color_lower[0])
                self.blue_g_lower.set(self.blue_area_color_lower[1])
                self.blue_r_lower.set(self.blue_area_color_lower[2])
                self.blue_b_upper.set(self.blue_area_color_upper[0])
                self.blue_g_upper.set(self.blue_area_color_upper[1])
                self.blue_r_upper.set(self.blue_area_color_upper[2])
                
                # 更新高级设置
                self.position_threshold = config["position_threshold"]
                self.max_click_delay = config["max_click_delay"]
                self.min_click_delay = config["min_click_delay"]
                self.cast_cooldown = config["cast_cooldown"]
                
                self.threshold_var.set(self.position_threshold)
                self.max_delay_var.set(self.max_click_delay)
                self.min_delay_var.set(self.min_click_delay)
                self.cast_cooldown_var.set(self.cast_cooldown)
                
                self.log(f"已从 {file_path} 加载配置")
        except Exception as e:
            self.log(f"加载配置出错: {str(e)}")
    
    def reset_config(self):
        """重置为默认配置"""
        if messagebox.askyesno("确认", "确定要重置所有设置到默认值吗？"):
            # 重置区域设置
            self.game_region = (int(self.screen_width/2-150), int(self.screen_height/2-250), 300, 500)
            self.region_x_var.set(self.game_region[0])
            self.region_y_var.set(self.game_region[1])
            self.region_w_var.set(self.game_region[2])
            self.region_h_var.set(self.game_region[3])
            
            # 重置颜色设置
            self.fish_color_lower = np.array([50, 80, 80])
            self.fish_color_upper = np.array([100, 150, 150])
            self.green_bar_color_lower = np.array([40, 160, 40])
            self.green_bar_color_upper = np.array([100, 255, 100])
            self.blue_area_color_lower = np.array([160, 100, 40])
            self.blue_area_color_upper = np.array([240, 180, 100])
            
            # 更新颜色输入框
            self.fish_b_lower.set(self.fish_color_lower[0])
            self.fish_g_lower.set(self.fish_color_lower[1])
            self.fish_r_lower.set(self.fish_color_lower[2])
            self.fish_b_upper.set(self.fish_color_upper[0])
            self.fish_g_upper.set(self.fish_color_upper[1])
            self.fish_r_upper.set(self.fish_color_upper[2])
            
            self.green_b_lower.set(self.green_bar_color_lower[0])
            self.green_g_lower.set(self.green_bar_color_lower[1])
            self.green_r_lower.set(self.green_bar_color_lower[2])
            self.green_b_upper.set(self.green_bar_color_upper[0])
            self.green_g_upper.set(self.green_bar_color_upper[1])
            self.green_r_upper.set(self.green_bar_color_upper[2])
            
            self.blue_b_lower.set(self.blue_area_color_lower[0])
            self.blue_g_lower.set(self.blue_area_color_lower[1])
            self.blue_r_lower.set(self.blue_area_color_lower[2])
            self.blue_b_upper.set(self.blue_area_color_upper[0])
            self.blue_g_upper.set(self.blue_area_color_upper[1])
            self.blue_r_upper.set(self.blue_area_color_upper[2])
            
            # 重置高级设置
            self.position_threshold = 10
            self.max_click_delay = 0.15
            self.min_click_delay = 0.01
            self.cast_cooldown = 5
            
            self.threshold_var.set(self.position_threshold)
            self.max_delay_var.set(self.max_click_delay)
            self.min_delay_var.set(self.min_click_delay)
            self.cast_cooldown_var.set(self.cast_cooldown)
            
            self.log("所有设置已重置为默认值")

# 主程序入口
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = StardewFishingBot(root)
        root.mainloop()
    except Exception as e:
        # 如果出现未捕获的异常，显示错误信息
        import traceback
        error_msg = f"错误: {str(e)}\n{traceback.format_exc()}"
        messagebox.showerror("程序错误", error_msg)
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(error_msg)
    
                
    
