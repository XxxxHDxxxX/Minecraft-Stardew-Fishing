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
        self.game_region = (int(self.screen_width/2-150), int(self.screen_height/2-250), 300, 500)
        
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