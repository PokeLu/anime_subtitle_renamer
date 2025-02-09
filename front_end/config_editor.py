import json
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext

from .utils import get_updated_config, read_config, write_config
from matcher import SubtitleMatcher

class ConfigEditor(tk.Tk):
    def __init__(self, config_file: str="config.json"):
        super().__init__()
        ConfigEditor.SETTING_SECTION = 'Settings'
        self.config_file = config_file
        self.config = {}
        # 创建一个字典来映射输入框和配置参数：{widget: config_param}
        self.entry_maping_dict = {}
        self.title("Configuration Editor")
        # self.geometry('500x500')
        
        # 添加组件...
        self.init_ui()
        # 加载初始参数
        self.load_initial_params(self.entry_maping_dict)
        # 创建 matcher
        self.matcher = SubtitleMatcher()
        self.matcher.load_config(self.config)
        
    def init_ui(self):
        self.geometry("800x400")  # 设置窗口初始大小
        self.minsize(800, 400)  # 设置窗口最小大小

        # 创建一个框架来容纳基本设置
        basic_frame = ttk.LabelFrame(self, text="基本设置")
        basic_frame.pack(padx=10, pady=10, fill='both', expand=True)
        
        # 设置各列的权重，使得它们能够均匀分布空间
        basic_frame.grid_columnconfigure(0, weight=1, minsize=50)  # 标签列
        basic_frame.grid_columnconfigure(1, weight=100, minsize=50)  # Combobox列
        basic_frame.grid_columnconfigure(2, weight=1, minsize=50)   # 标签列
        basic_frame.grid_columnconfigure(3, weight=100, minsize=50)  # Combobox列
        # basic_frame.grid_columnconfigure(4, weight=1, minsize=150)  # 其他内容列

        # 基本设置标签页控件布局
        ttk.Label(basic_frame, text="是否清除原文件:", justify='left').grid(column=0, row=0, padx=5, pady=5, sticky='w')
        self.clear_files_combo = ttk.Combobox(basic_frame, values=[True, False])
        self.clear_files_combo.grid(column=1, row=0, padx=5, pady=5, sticky='ew')
        self.entry_maping_dict[self.clear_files_combo] = "clear_files"
        
        ttk.Label(basic_frame, text="Debug模式:", justify='left').grid(column=2, row=0, padx=5, pady=5, sticky='w')
        self.debug_mode_combo = ttk.Combobox(basic_frame, values=[True, False])
        self.debug_mode_combo.grid(column=3, row=0, padx=5, pady=5, sticky='ew')
        self.entry_maping_dict[self.debug_mode_combo] = "debug_mode"
        
        ttk.Label(basic_frame, text="视频所在目录:", justify='left').grid(column=0, row=1, padx=5, pady=5, sticky='w')
        self.video_dir_entry = ttk.Entry(basic_frame)
        self.video_dir_entry.grid(column=1, columnspan=3, row=1, padx=5, pady=5, sticky='ew')
        self.entry_maping_dict[self.video_dir_entry] = "video_dir"
        
        ttk.Label(basic_frame, text="字幕所在目录:", justify='left').grid(column=0, row=2, padx=5, pady=5, sticky='w')
        self.sub_src_dir_entry = ttk.Entry(basic_frame)
        self.sub_src_dir_entry.grid(column=1, columnspan=3, row=2, padx=5, pady=5, sticky='ew')
        self.entry_maping_dict[self.sub_src_dir_entry] = "sub_src_dir"
        
        ttk.Label(basic_frame, text="字幕目标目录:", justify='left').grid(column=0, row=3, padx=5, pady=5, sticky='w')
        self.sub_tar_dir_entry = ttk.Entry(basic_frame)
        self.sub_tar_dir_entry.grid(column=1, columnspan=3, row=3, padx=5, pady=5, sticky='ew')
        self.entry_maping_dict[self.sub_tar_dir_entry] = "sub_tar_dir"

        # 创建一个框架来容纳高级设置
        advanced_frame = ttk.LabelFrame(self, text="高级设置")
        advanced_frame.pack(padx=10, pady=10, fill='both', expand=True)
        
        # 设置各列的权重，使得它们能够均匀分布空间
        advanced_frame.grid_columnconfigure(0, weight=1, minsize=50)  # 标签列
        advanced_frame.grid_columnconfigure(1, weight=100, minsize=50)  # Combobox列
        advanced_frame.grid_columnconfigure(2, weight=1, minsize=50)   # 标签列
        advanced_frame.grid_columnconfigure(3, weight=100, minsize=50)  # Combobox列
        # basic_frame.grid_columnconfigure(4, weight=1, minsize=150)  # 其他内容列

        # 高级设置标签页控件布局（省略了部分代码以简化）
        ttk.Label(advanced_frame, text="匹配视频格式:", justify='left').grid(column=0, row=0, padx=5, pady=5, sticky='w')
        self.video_ext_entry = ttk.Entry(advanced_frame)
        self.video_ext_entry.grid(column=1, columnspan=3, row=0, padx=5, pady=5, sticky='ew')
        self.entry_maping_dict[self.video_ext_entry] = "video_ext"
        
        ttk.Label(advanced_frame, text="匹配字幕格式:", justify='left').grid(column=0, row=1, padx=5, pady=5, sticky='w')
        self.subtitle_ext_entry = ttk.Entry(advanced_frame)
        self.subtitle_ext_entry.grid(column=1, columnspan=3, row=1, padx=5, pady=5, sticky='ew')
        self.entry_maping_dict[self.subtitle_ext_entry] = "subtitle_ext"
        
        ttk.Label(advanced_frame, text="匹配模式:", justify='left').grid(column=0, row=2, padx=5, pady=5, sticky='w')
        self.match_method_combo = ttk.Combobox(advanced_frame, values=["ab", "ai", "raw"])
        self.match_method_combo.grid(column=1, row=2, padx=5, pady=5, sticky='ew')
        self.entry_maping_dict[self.match_method_combo] = "match_method"
        
        ttk.Label(advanced_frame, text="视频集数位置:", justify='left').grid(column=0, row=3, padx=5, pady=5, sticky='w')
        self.match_pos_combo = ttk.Entry(advanced_frame)
        self.match_pos_combo.grid(column=1, row=3, padx=5, pady=5, sticky='ew')
        self.entry_maping_dict[self.match_pos_combo] = "video_match_pos"
        
        ttk.Label(advanced_frame, text="视频匹配正则:", justify='left').grid(column=2, row=3, padx=5, pady=5, sticky='w')
        self.pattern_entry = ttk.Entry(advanced_frame)
        self.pattern_entry.grid(column=3, row=3, padx=5, pady=5, sticky='ew')
        self.entry_maping_dict[self.pattern_entry] = "video_pattern"

        ttk.Label(advanced_frame, text="字幕集数位置:", justify='left').grid(column=0, row=4, padx=5, pady=5, sticky='w')
        self.match_pos_combo = ttk.Entry(advanced_frame)
        self.match_pos_combo.grid(column=1, row=4, padx=5, pady=5, sticky='ew')
        self.entry_maping_dict[self.match_pos_combo] = "sub_match_pos"
        
        ttk.Label(advanced_frame, text="字幕匹配正则:", justify='left').grid(column=2, row=4, padx=5, pady=5, sticky='w')
        self.pattern_entry = ttk.Entry(advanced_frame)
        self.pattern_entry.grid(column=3, row=4, padx=5, pady=5, sticky='ew')
        self.entry_maping_dict[self.pattern_entry] = "sub_pattern"
        
        # 创建一个容器用于放置按钮
        button_container = ttk.Frame(self)
        button_container.pack(pady=10)

        # 创建应用按钮
        apply_button = ttk.Button(button_container, text="应用", command=self.apply_changes_with_messages)
        apply_button.grid(row=0, column=0, padx=5)

        # 创建运行按钮
        run_button = ttk.Button(button_container, text="运行", command=self.run_match)
        run_button.grid(row=0, column=1, padx=5)
        
        # 创建保存按钮
        save_button = ttk.Button(button_container, text="保存", command=self.save_changes_with_messages)
        save_button.grid(row=0, column=2, padx=5)
        
    # 将json中的数值转换为tkinter支持的格式
    @staticmethod
    def process_tk_str(value):
        if isinstance(value, bool):
            return "True" if value else "False"
        elif isinstance(value, list) or isinstance(value, tuple) or isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return value
    
    # 将tkinter获取的字符串转换回json支持的格式
    @staticmethod
    def convert_tk_str(value):
        if value == "True":
            return True
        elif value == "False":
            return False
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
        
    def popup_long_message(self, title:str, message:str):
        # 创建弹窗
        popup = tk.Toplevel(self)
        popup.title(title)
        
        # 设置弹窗的最小大小
        popup.minsize(300, 200)
        
        text_area = scrolledtext.ScrolledText(popup, wrap=tk.WORD)
        text_area.insert(tk.INSERT, message)
        
        # 将文本框添加到弹窗中，并使其随窗口大小变化
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建确定按钮
        ok_button = tk.Button(popup, text="确定", command=popup.destroy)
        ok_button.pack(pady=10)
        
    def apply_changes(self):
        # 需要更新的配置参数和新值，{config_param: new_config_value}
        updating_config = {}
        for entry, config_param in self.entry_maping_dict.items():
            if entry.get():
                updating_config[config_param] = self.convert_tk_str(entry.get())
        self.config = get_updated_config(self.config, **updating_config)
        self.matcher.load_config(self.config)
        
    def apply_changes_with_messages(self):
        self.apply_changes()
        messagebox.showinfo("成功", "参数已更新")
            
    def save_changes_with_messages(self):
        self.apply_changes()
        write_config(self.config_file, self.config)
        messagebox.showinfo("成功", "参数已保存")
        
    def run_match(self):
        self.apply_changes()
        if self.config["clear_files"]:
            self.matcher.clear_files(self.config["sub_tar_dir"], self.config["subtitle_ext"])
        sub_rename_dict = self.matcher(self.config["video_dir"], self.config["sub_src_dir"], self.config["sub_tar_dir"])
        if self.config["debug_mode"]:
            rename_msg = "\n".join([f"{key}\n-->\n{value}\n" for key, value in sub_rename_dict.items()])
            self.popup_long_message("重命名信息", rename_msg)
        else:
            messagebox.showinfo("成功", "重命名已完成")
        
    # 加载初始参数
    def load_initial_params(self, entry_maping_dict: dict):
        self.config = read_config(self.config_file)
        
        for entry, config_param in entry_maping_dict.items():
            if not isinstance(entry, ttk.Entry) and not isinstance(entry, ttk.Combobox):
                print(f"无效的 entry 或 config_param 类型: {entry}, {config_param}")
                continue
            
            try: 
                value = self.process_tk_str(self.config[config_param])
            except KeyError:
                print(f"配置项 '{config_param}' 未找到")
                messagebox.showerror("错误", f"配置项 '{config_param}' 未找到")
                continue
            
            if isinstance(entry, ttk.Entry):
                entry.insert(0, value)
            elif isinstance(entry, ttk.Combobox):
                try: 
                    combo_idx = entry['values'].index(value)
                    entry.set(combo_idx)
                except:
                    messagebox.showerror("错误", f"配置项 '{entry.cget("text")}' 的值 '{value}' 不在可选项中, 默认设定为'{entry['values'][0]}'")
                    entry.set(0)