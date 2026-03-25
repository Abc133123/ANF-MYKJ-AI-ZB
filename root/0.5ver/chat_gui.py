import tkinter as tk
from tkinter import ttk, scrolledtext

class ChatGUI:
    def __init__(self, on_send_callback, on_clear_callback, on_voice_toggle_callback):
        self.root = tk.Tk()
        self.root.title("长月 - 贝塔 AI 对话")
        
        self.root.attributes('-alpha', 0.85)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#1a1a2e')
        
        self.root.geometry("500x700+100+100")
        
        self.on_send = on_send_callback
        self.on_clear = on_clear_callback
        self.on_voice_toggle = on_voice_toggle_callback
        
        self.setup_ui()
        
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background='#1a1a2e')
        style.configure('TLabel', background='#1a1a2e', foreground='#e0e0e0', font=('Microsoft YaHei UI', 10))
        style.configure('TButton', background='#4a4a6a', foreground='#ffffff', font=('Microsoft YaHei UI', 10), borderwidth=0)
        style.map('TButton', background=[('active', '#5a5a8a')])
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text="长月 - 贝塔 AI", font=('Microsoft YaHei UI', 14, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        status_label = ttk.Label(header_frame, text="● 未连接", foreground='#ff6b6b')
        status_label.pack(side=tk.RIGHT)
        self.status_label = status_label
        
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            bg='#0f0f1a',
            fg='#e0e0e0',
            font=('Microsoft YaHei UI', 11),
            wrap=tk.WORD,
            padx=10,
            pady=10,
            borderwidth=0,
            highlightthickness=0
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display.tag_config('user', foreground='#4ecdc4', font=('Microsoft YaHei UI', 11, 'bold'))
        self.chat_display.tag_config('assistant', foreground='#ffe66d', font=('Microsoft YaHei UI', 11))
        self.chat_display.tag_config('system', foreground='#95a5a6', font=('Microsoft YaHei UI', 9, 'italic'))
        self.chat_display.tag_config('error', foreground='#ff6b6b', font=('Microsoft YaHei UI', 10))
        
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.input_text = tk.Text(
            input_frame,
            bg='#2a2a4a',
            fg='#ffffff',
            font=('Microsoft YaHei UI', 11),
            height=3,
            padx=10,
            pady=8,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground='#4a4a6a',
            highlightcolor='#6a6a9a'
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.input_text.bind('<Return>', lambda e: self.send_message())
        self.input_text.bind('<Shift-Return>', lambda e: None)
        
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        send_button = ttk.Button(button_frame, text="发送", command=self.send_message)
        send_button.pack(fill=tk.X, pady=(0, 5))
        
        clear_button = ttk.Button(button_frame, text="清空", command=self.clear_chat)
        clear_button.pack(fill=tk.X, pady=(0, 5))
        
        voice_button = ttk.Button(button_frame, text="语音", command=self.toggle_voice)
        voice_button.pack(fill=tk.X)
        
    def update_status(self, text, color):
        self.status_label.config(text=text, foreground=color)
        
    def add_user_message(self, message):
        self.chat_display.insert(tk.END, f"你: {message}\n\n", 'user')
        self.chat_display.see(tk.END)
    
    def add_assistant_message(self, message):
        self.chat_display.insert(tk.END, f"长月: {message}\n\n", 'assistant')
        self.chat_display.see(tk.END)
    
    def add_system_message(self, message):
        self.chat_display.insert(tk.END, f"[系统] {message}\n\n", 'system')
        self.chat_display.see(tk.END)
    
    def add_error_message(self, message):
        self.chat_display.insert(tk.END, f"[错误] {message}\n\n", 'error')
        self.chat_display.see(tk.END)
    
    def send_message(self):
        user_input = self.input_text.get(1.0, tk.END).strip()
        if user_input:
            self.input_text.delete(1.0, tk.END)
            if self.on_send:
                self.on_send(user_input)
    
    def clear_chat(self):
        if self.on_clear:
            self.on_clear()
    
    def toggle_voice(self):
        if self.on_voice_toggle:
            self.on_voice_toggle()
    
    def run(self):
        self.root.mainloop()