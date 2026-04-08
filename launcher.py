import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import os
import sys
import webbrowser
import time
from pathlib import Path


class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片爬虫 4.0 - 启动器")
        self.root.geometry("700x550")
        self.root.resizable(True, True)
        
        self.base_dir = Path(__file__).parent.absolute()
        self.backend_dir = self.base_dir / "backend"
        self.frontend_dir = self.base_dir / "frontend"
        self.venv_dir = self.base_dir / ".venv"
        
        self.backend_process = None
        self.frontend_process = None
        
        self.backend_running = False
        self.frontend_running = False
        
        self.setup_ui()
        self.check_environment()
        
    def setup_ui(self):
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Microsoft YaHei", 16, "bold"))
        style.configure("Status.TLabel", font=("Microsoft YaHei", 10))
        style.configure("Service.TLabelframe.Label", font=("Microsoft YaHei", 11, "bold"))
        
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame, 
            text="🕷️ 图片爬虫 4.0 启动器", 
            style="Title.TLabel"
        )
        title_label.pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(
            title_frame, 
            text="● 就绪", 
            style="Status.TLabel",
            foreground="gray"
        )
        self.status_label.pack(side=tk.RIGHT)
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        backend_frame = ttk.LabelFrame(
            main_frame, 
            text="后端服务 (FastAPI - 端口 8000)", 
            style="Service.TLabelframe",
            padding="10"
        )
        backend_frame.pack(fill=tk.X, pady=(0, 10))
        
        backend_status_frame = ttk.Frame(backend_frame)
        backend_status_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.backend_status_label = ttk.Label(
            backend_status_frame, 
            text="状态: 未启动", 
            foreground="gray"
        )
        self.backend_status_label.pack(side=tk.LEFT)
        
        self.backend_url_label = ttk.Label(
            backend_status_frame, 
            text="http://localhost:8000", 
            foreground="blue",
            cursor="hand2"
        )
        self.backend_url_label.pack(side=tk.RIGHT)
        self.backend_url_label.bind("<Button-1>", lambda e: self.open_url("http://localhost:8000"))
        
        backend_btn_frame = ttk.Frame(backend_frame)
        backend_btn_frame.pack(fill=tk.X)
        
        self.backend_start_btn = ttk.Button(
            backend_btn_frame, 
            text="▶ 启动后端", 
            command=self.start_backend,
            width=15
        )
        self.backend_start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.backend_stop_btn = ttk.Button(
            backend_btn_frame, 
            text="⏹ 停止后端", 
            command=self.stop_backend,
            state=tk.DISABLED,
            width=15
        )
        self.backend_stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            backend_btn_frame, 
            text="📖 API文档", 
            command=lambda: self.open_url("http://localhost:8000/docs"),
            width=12
        ).pack(side=tk.LEFT)
        
        frontend_frame = ttk.LabelFrame(
            main_frame, 
            text="前端服务 (Vue.js - 端口 3000)", 
            style="Service.TLabelframe",
            padding="10"
        )
        frontend_frame.pack(fill=tk.X, pady=(0, 10))
        
        frontend_status_frame = ttk.Frame(frontend_frame)
        frontend_status_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.frontend_status_label = ttk.Label(
            frontend_status_frame, 
            text="状态: 未启动", 
            foreground="gray"
        )
        self.frontend_status_label.pack(side=tk.LEFT)
        
        self.frontend_url_label = ttk.Label(
            frontend_status_frame, 
            text="http://localhost:3000", 
            foreground="blue",
            cursor="hand2"
        )
        self.frontend_url_label.pack(side=tk.RIGHT)
        self.frontend_url_label.bind("<Button-1>", lambda e: self.open_url("http://localhost:3000"))
        
        frontend_btn_frame = ttk.Frame(frontend_frame)
        frontend_btn_frame.pack(fill=tk.X)
        
        self.frontend_start_btn = ttk.Button(
            frontend_btn_frame, 
            text="▶ 启动前端", 
            command=self.start_frontend,
            width=15
        )
        self.frontend_start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.frontend_stop_btn = ttk.Button(
            frontend_btn_frame, 
            text="⏹ 停止前端", 
            command=self.stop_frontend,
            state=tk.DISABLED,
            width=15
        )
        self.frontend_stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            frontend_btn_frame, 
            text="🌐 打开网页", 
            command=lambda: self.open_url("http://localhost:3000"),
            width=12
        ).pack(side=tk.LEFT)
        
        quick_frame = ttk.LabelFrame(
            main_frame, 
            text="快捷操作", 
            style="Service.TLabelframe",
            padding="10"
        )
        quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            quick_frame, 
            text="🚀 一键启动全部", 
            command=self.start_all,
            width=20
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            quick_frame, 
            text="⏹ 一键停止全部", 
            command=self.stop_all,
            width=20
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            quick_frame, 
            text="🔄 刷新状态", 
            command=self.refresh_status,
            width=15
        ).pack(side=tk.LEFT)
        
        log_frame = ttk.LabelFrame(
            main_frame, 
            text="运行日志", 
            style="Service.TLabelframe",
            padding="5"
        )
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=10, 
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.log_text.tag_configure("info", foreground="#4ec9b0")
        self.log_text.tag_configure("success", foreground="#4fc3f7")
        self.log_text.tag_configure("error", foreground="#f44747")
        self.log_text.tag_configure("warning", foreground="#ffcc00")
        
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)
        
        ttk.Button(
            bottom_frame, 
            text="🗑️ 清空日志", 
            command=self.clear_log,
            width=12
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            bottom_frame, 
            text="❌ 退出", 
            command=self.on_closing,
            width=10
        ).pack(side=tk.RIGHT)
        
    def log(self, message, level="info"):
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, full_message, level)
        self.log_text.see(tk.END)
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.log("日志已清空", "info")
        
    def check_environment(self):
        self.log("正在检查运行环境...", "info")
        
        if not self.backend_dir.exists():
            self.log("警告: backend 目录不存在", "warning")
            
        if not self.frontend_dir.exists():
            self.log("警告: frontend 目录不存在", "warning")
            
        if self.venv_dir.exists():
            self.log("检测到虚拟环境: .venv", "success")
        else:
            self.log("未检测到虚拟环境，将使用系统 Python", "warning")
            
        node_modules = self.base_dir / "node_modules"
        if node_modules.exists():
            self.log("前端依赖已安装", "success")
        else:
            self.log("前端依赖未安装，首次启动前请运行: npm install", "warning")
            
        self.log("环境检查完成", "info")
        
    def get_python_executable(self):
        if sys.platform == "win32":
            python_exe = self.venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = self.venv_dir / "bin" / "python"
            
        if python_exe.exists():
            return str(python_exe)
        return sys.executable
        
    def get_npm_command(self):
        if sys.platform == "win32":
            return "npm.cmd"
        return "npm"
        
    def start_backend(self):
        if self.backend_running:
            self.log("后端服务已在运行中", "warning")
            return
            
        self.log("正在启动后端服务...", "info")
        
        def run_backend():
            try:
                python_exe = self.get_python_executable()
                uvicorn_cmd = [
                    python_exe, "-m", "uvicorn", 
                    "app.main:app", 
                    "--host", "0.0.0.0", 
                    "--port", "8000",
                    "--reload"
                ]
                
                self.backend_process = subprocess.Popen(
                    uvicorn_cmd,
                    cwd=str(self.backend_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
                )
                
                time.sleep(2)
                
                if self.backend_process.poll() is None:
                    self.backend_running = True
                    self.root.after(0, self.update_backend_status, True)
                    self.log("后端服务启动成功 - http://localhost:8000", "success")
                else:
                    self.root.after(0, self.update_backend_status, False)
                    self.log("后端服务启动失败", "error")
                    
            except Exception as e:
                self.root.after(0, self.update_backend_status, False)
                self.log(f"启动后端服务时出错: {str(e)}", "error")
                
        threading.Thread(target=run_backend, daemon=True).start()
        
    def stop_backend(self):
        if not self.backend_running or self.backend_process is None:
            self.log("后端服务未运行", "warning")
            return
            
        try:
            self.log("正在停止后端服务...", "info")
            if sys.platform == "win32":
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(self.backend_process.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                self.backend_process.terminate()
                
            self.backend_process = None
            self.backend_running = False
            self.update_backend_status(False)
            self.log("后端服务已停止", "success")
        except Exception as e:
            self.log(f"停止后端服务时出错: {str(e)}", "error")
            
    def start_frontend(self):
        if self.frontend_running:
            self.log("前端服务已在运行中", "warning")
            return
            
        node_modules = self.base_dir / "node_modules"
        if not node_modules.exists():
            self.log("前端依赖未安装，请先运行: npm install", "error")
            messagebox.showwarning(
                "提示", 
                "前端依赖未安装！\n\n请在项目根目录运行以下命令安装依赖：\nnpm install"
            )
            return
            
        self.log("正在启动前端服务...", "info")
        
        def run_frontend():
            try:
                npm_cmd = self.get_npm_command()
                self.frontend_process = subprocess.Popen(
                    [npm_cmd, "run", "dev"],
                    cwd=str(self.base_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
                )
                
                time.sleep(3)
                
                if self.frontend_process.poll() is None:
                    self.frontend_running = True
                    self.root.after(0, self.update_frontend_status, True)
                    self.log("前端服务启动成功 - http://localhost:3000", "success")
                else:
                    self.root.after(0, self.update_frontend_status, False)
                    self.log("前端服务启动失败", "error")
                    
            except Exception as e:
                self.root.after(0, self.update_frontend_status, False)
                self.log(f"启动前端服务时出错: {str(e)}", "error")
                
        threading.Thread(target=run_frontend, daemon=True).start()
        
    def stop_frontend(self):
        if not self.frontend_running or self.frontend_process is None:
            self.log("前端服务未运行", "warning")
            return
            
        try:
            self.log("正在停止前端服务...", "info")
            if sys.platform == "win32":
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(self.frontend_process.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                self.frontend_process.terminate()
                
            self.frontend_process = None
            self.frontend_running = False
            self.update_frontend_status(False)
            self.log("前端服务已停止", "success")
        except Exception as e:
            self.log(f"停止前端服务时出错: {str(e)}", "error")
            
    def update_backend_status(self, running):
        if running:
            self.backend_status_label.config(text="状态: 运行中", foreground="green")
            self.backend_start_btn.config(state=tk.DISABLED)
            self.backend_stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="● 后端运行中", foreground="green")
        else:
            self.backend_status_label.config(text="状态: 未启动", foreground="gray")
            self.backend_start_btn.config(state=tk.NORMAL)
            self.backend_stop_btn.config(state=tk.DISABLED)
            self.update_overall_status()
            
    def update_frontend_status(self, running):
        if running:
            self.frontend_status_label.config(text="状态: 运行中", foreground="green")
            self.frontend_start_btn.config(state=tk.DISABLED)
            self.frontend_stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="● 前端运行中", foreground="green")
        else:
            self.frontend_status_label.config(text="状态: 未启动", foreground="gray")
            self.frontend_start_btn.config(state=tk.NORMAL)
            self.frontend_stop_btn.config(state=tk.DISABLED)
            self.update_overall_status()
            
    def update_overall_status(self):
        if self.backend_running and self.frontend_running:
            self.status_label.config(text="● 全部运行中", foreground="green")
        elif self.backend_running or self.frontend_running:
            self.status_label.config(text="● 部分运行中", foreground="orange")
        else:
            self.status_label.config(text="● 就绪", foreground="gray")
            
    def start_all(self):
        self.log("正在启动所有服务...", "info")
        self.start_backend()
        time.sleep(2)
        self.start_frontend()
        
    def stop_all(self):
        self.log("正在停止所有服务...", "info")
        self.stop_backend()
        self.stop_frontend()
        
    def refresh_status(self):
        self.log("刷新服务状态...", "info")
        self.update_overall_status()
        self.log("状态已刷新", "info")
        
    def open_url(self, url):
        try:
            webbrowser.open(url)
            self.log(f"已打开: {url}", "info")
        except Exception as e:
            self.log(f"打开URL失败: {str(e)}", "error")
            
    def on_closing(self):
        if self.backend_running or self.frontend_running:
            if messagebox.askokcancel("退出", "有服务正在运行，确定要退出吗？\n退出将停止所有服务。"):
                self.stop_all()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = LauncherApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
