"""
AI Companion - 情感AI伴侣
一个能表达情绪的AI对话伙伴，开源可替换头像
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import re
import os
from pathlib import Path
from PIL import Image, ImageTk
import threading


class AICompanion:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Companion")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        
        # 加载配置
        self.config = self.load_json("config.json")
        self.prompt_config = self.load_json("prompt.json")
        
        self.provider = self.config.get("provider", "deepseek")
        self.api_key = self.config.get("api_key", "")
        self.api_url = self.config.get("api_url", "https://api.deepseek.com/v1/chat/completions")
        self.model = self.config.get("model", "deepseek-chat")
        self.personality = self.config.get("personality", "温柔体贴的小助手")
        self.debug = self.config.get("debug", False)
        
        # 从 prompt.json 加载情绪配置
        self.emotions = self.prompt_config.get("emotions", {})
        self.emotion_pattern = self.prompt_config.get("emotion_pattern", "")
        
        # 资源路径
        self.assets_base = Path(__file__).parent.parent / "assets"
        self.characters_dir = self.assets_base / "characters"
        self.emotions_base = self.assets_base / "emotions"
        self.current_style = self.config.get("character_style", "luna")
        self.current_emotion = "默认"
        
        # 对话历史
        self.messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        
        # UI
        self.setup_ui()
        self.load_emotion("默认")
        
    def load_json(self, filename):
        """加载JSON配置文件"""
        path = Path(__file__).parent.parent / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def get_system_prompt(self):
        """生成系统提示词"""
        template = self.prompt_config.get("system_prompt", "")
        emotions_list = " ".join([f"[{e}]" for e in self.emotions.keys() if e != "说话"])
        # 角色名首字母大写
        name = self.current_style.capitalize()
        return template.format(name=name, personality=self.personality, emotions=emotions_list)

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 头像区域
        avatar_frame = ttk.Frame(main_frame)
        avatar_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.avatar_label = ttk.Label(avatar_frame)
        self.avatar_label.pack()
        
        self.emotion_label = ttk.Label(avatar_frame, text="当前情绪：默认", font=("微软雅黑", 10))
        self.emotion_label.pack()
        
        # 聊天区域
        chat_frame = ttk.LabelFrame(main_frame, text="对话")
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, height=15, state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 输入区域
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind("<Return>", self.send_message)
        
        self.send_button = ttk.Button(input_frame, text="发送", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 底部按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(bottom_frame, text="设置", command=self.show_settings).pack(side=tk.LEFT)

    def get_available_styles(self):
        """获取可用的角色风格列表"""
        styles = []
        if self.emotions_base.exists():
            for d in self.emotions_base.iterdir():
                if d.is_dir():
                    styles.append(d.name)
        return sorted(styles) if styles else ["style1"]

    def load_emotion(self, emotion):
        """加载情绪对应的头像"""
        self.current_emotion = emotion
        
        # 查找对应的图片文件
        style_dir = self.emotions_base / self.current_style
        if emotion in self.emotions:
            img_path = style_dir / self.emotions[emotion]
        else:
            img_path = style_dir / "default.png"
        
        # 如果图片不存在，创建一个占位图
        if not img_path.exists():
            self.create_placeholder_emotion(emotion)
        
        # 加载并显示图片
        try:
            img = Image.open(img_path)
            img = img.resize((150, 150), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.avatar_label.configure(image=photo)
            self.avatar_label.image = photo  # 保持引用
            self.emotion_label.configure(text=f"当前情绪：{emotion}")
        except Exception as e:
            print(f"加载图片失败: {e}")

    def create_placeholder_emotion(self, emotion):
        """创建占位情绪图片（如果没有真实图片）"""
        colors = {
            "默认": "#4A90D9", "高兴": "#FFD700", "生气": "#FF4444",
            "悲伤": "#4169E1", "惊讶": "#FF69B4", "害羞": "#FFB6C1",
            "思考": "#9370DB", "说话": "#98FB98", "困惑": "#DDA0DD",
            "得意": "#FFA500", "无聊": "#808080", "兴奋": "#FF1493",
            "委屈": "#87CEEB",
        }
        
        color = colors.get(emotion, "#4A90D9")
        img = Image.new('RGB', (150, 150), color)
        
        # 保存到当前风格目录
        style_dir = self.emotions_base / self.current_style
        style_dir.mkdir(parents=True, exist_ok=True)
        img_path = style_dir / self.emotions.get(emotion, "default.png")
        img.save(img_path)

    def parse_emotion(self, text):
        """从AI回复中解析情绪标签"""
        if not self.emotion_pattern:
            return "默认"
        pattern = rf'\[{self.emotion_pattern}\]'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        return "默认"

    def clean_response(self, text):
        """移除回复中的情绪标签"""
        if not self.emotion_pattern:
            return text
        pattern = rf'\[{self.emotion_pattern}\]'
        return re.sub(pattern, '', text).strip()

    def send_message(self, event=None):
        """发送消息"""
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
        
        # 显示用户消息
        self.display_message("你", user_input)
        self.input_entry.delete(0, tk.END)
        
        # 禁用输入
        self.send_button.configure(state=tk.DISABLED)
        self.input_entry.configure(state=tk.DISABLED)
        
        # 异步调用AI
        threading.Thread(target=self.get_ai_response, args=(user_input,), daemon=True).start()

    def get_ai_response(self, user_input):
        """获取AI回复（假流式）"""
        try:
            self.messages.append({"role": "user", "content": user_input})
            
            headers = {"Content-Type": "application/json"}
            if self.provider == "deepseek" and self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # 绕过 localhost 代理
            proxies = {"http": None, "https": None} if "localhost" in self.api_url or "127.0.0.1" in self.api_url else None
            
            data = {
                "model": self.model,
                "messages": self.messages,
                "temperature": 0.8,
                "max_tokens": 200
            }
            
            # 显示"说话中"状态
            self.root.after(0, lambda: self.load_emotion("说话"))
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30, proxies=proxies)
            response.raise_for_status()
            
            ai_response = response.json()["choices"][0]["message"]["content"]
            self.messages.append({"role": "assistant", "content": ai_response})
            
            # 解析情绪
            emotion = self.parse_emotion(ai_response)
            clean_text = self.clean_response(ai_response)
            
            # debug模式显示原始标签
            if self.debug:
                clean_text = f"[{emotion}] {clean_text}"
            
            # 假流式：一个字一个字输出
            self.root.after(0, lambda: self.fake_stream(emotion, clean_text))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.handle_error(msg))

    def fake_stream(self, emotion, text):
        """假流式输出"""
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "AI：")
        self.chat_display.configure(state=tk.DISABLED)
        
        self.stream_text = text
        self.stream_index = 0
        self.stream_emotion = emotion
        self.type_next_char()

    def type_next_char(self):
        """逐字输出"""
        if self.stream_index < len(self.stream_text):
            char = self.stream_text[self.stream_index]
            self.chat_display.configure(state=tk.NORMAL)
            self.chat_display.insert(tk.END, char)
            self.chat_display.configure(state=tk.DISABLED)
            self.chat_display.see(tk.END)
            self.stream_index += 1
            self.root.after(50, self.type_next_char)  # 50ms 一个字
        else:
            # 完成
            self.chat_display.configure(state=tk.NORMAL)
            self.chat_display.insert(tk.END, "\n\n")
            self.chat_display.configure(state=tk.DISABLED)
            self.load_emotion(self.stream_emotion)
            self.send_button.configure(state=tk.NORMAL)
            self.input_entry.configure(state=tk.NORMAL)
            self.input_entry.focus()

    def handle_error(self, error_msg):
        """处理错误"""
        self.display_message("系统", f"出错了：{error_msg}")
        self.send_button.configure(state=tk.NORMAL)
        self.input_entry.configure(state=tk.NORMAL)

    def display_message(self, sender, message):
        """显示消息到聊天区域"""
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}：{message}\n\n")
        self.chat_display.configure(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def show_settings(self):
        """显示设置对话框"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("350x450")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 角色选择（下拉菜单）
        ttk.Label(settings_window, text="角色：").pack(pady=5)
        styles = self.get_available_styles()
        style_var = tk.StringVar(value=self.current_style)
        style_combo = ttk.Combobox(settings_window, textvariable=style_var, values=styles, state="readonly", width=30)
        style_combo.pack(pady=5)
        
        # 添加新角色按钮
        def add_character():
            from tkinter import simpledialog
            name = simpledialog.askstring("添加角色", "输入角色名称：", parent=settings_window)
            if name and name not in styles:
                # 创建角色目录
                new_dir = self.emotions_base / name
                new_dir.mkdir(parents=True, exist_ok=True)
                # 更新下拉菜单
                styles.append(name)
                style_combo['values'] = styles
                style_var.set(name)
                messagebox.showinfo("提示", f"角色 '{name}' 已添加，请在 assets/emotions/{name}/ 中放入头像图片")
        
        ttk.Button(settings_window, text="添加新角色", command=add_character).pack(pady=5)
        
        # Provider选择
        ttk.Label(settings_window, text="AI提供商：").pack(pady=5)
        provider_var = tk.StringVar(value=self.provider)
        provider_frame = ttk.Frame(settings_window)
        provider_frame.pack()
        ttk.Radiobutton(provider_frame, text="DeepSeek", variable=provider_var, value="deepseek").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(provider_frame, text="Ollama (本地)", variable=provider_var, value="ollama").pack(side=tk.LEFT, padx=10)
        
        # API URL
        ttk.Label(settings_window, text="API地址：").pack(pady=5)
        api_url_entry = ttk.Entry(settings_window, width=40)
        api_url_entry.insert(0, self.api_url)
        api_url_entry.pack(pady=5)
        
        # Model
        ttk.Label(settings_window, text="模型名称：").pack(pady=5)
        model_entry = ttk.Entry(settings_window, width=40)
        model_entry.insert(0, self.model)
        model_entry.pack(pady=5)
        
        # 性格设置
        ttk.Label(settings_window, text="AI性格：").pack(pady=5)
        personality_entry = ttk.Entry(settings_window, width=40)
        personality_entry.insert(0, self.personality)
        personality_entry.pack(pady=5)
        
        # Debug模式
        debug_var = tk.BooleanVar(value=self.debug)
        ttk.Checkbutton(settings_window, text="Debug模式（显示情绪标签）", variable=debug_var).pack(pady=5)
        
        def save_settings():
            self.provider = provider_var.get()
            self.api_url = api_url_entry.get()
            self.model = model_entry.get()
            self.personality = personality_entry.get()
            self.debug = debug_var.get()
            
            # 更新角色风格
            new_style = style_var.get()
            if new_style != self.current_style:
                self.current_style = new_style
                self.load_emotion(self.current_emotion)
                # 更新系统提示词并插入角色切换提示
                self.messages[0]["content"] = self.get_system_prompt()
                new_name = new_style.capitalize()
                self.messages.append({"role": "system", "content": f"你现在是{new_name}了，请用新身份继续对话。"})
                self.display_message("系统", f"角色已切换为 {new_name}")
            
            # 根据provider设置默认值
            if self.provider == "ollama":
                self.api_key = ""
                if not self.api_url or "deepseek" in self.api_url:
                    self.api_url = "http://localhost:11434/v1/chat/completions"
                if not self.model or "deepseek" in self.model:
                    self.model = "qwen3:4b"
            
            # 更新系统提示词
            self.messages[0]["content"] = self.get_system_prompt()
            # 保存到配置文件
            self.config["provider"] = self.provider
            self.config["api_url"] = self.api_url
            self.config["model"] = self.model
            self.config["personality"] = self.personality
            self.config["character_style"] = self.current_style
            self.config["debug"] = self.debug
            config_path = Path(__file__).parent.parent / "config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            settings_window.destroy()
            messagebox.showinfo("提示", "设置已保存！")
        
        ttk.Button(settings_window, text="保存", command=save_settings).pack(pady=10)

def main():
    root = tk.Tk()
    app = AICompanion(root)
    root.mainloop()

if __name__ == "__main__":
    main()