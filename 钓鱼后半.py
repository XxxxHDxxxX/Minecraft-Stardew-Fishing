def capture_screen(self, region=None):
        """捕获指定区域的屏幕"""
        if region:
            screenshot = ImageGrab.grab(bbox=region)
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