# -*- coding: utf-8 -*-
import sys
import os
import json
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QComboBox, QMessageBox, QProgressBar)
from PyQt5.QtCore import QThread, pyqtSignal

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")


class Worker(QThread):
    """后台工作线程"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    progress_signal = pyqtSignal(int)

    def __init__(self, token, config, template_name, template_dir, template_config):
        super().__init__()
        self.token = token
        self.config = config
        self.template_name = template_name
        self.template_dir = template_dir
        self.template_config = template_config

    def run(self):
        try:
            self.progress_signal.emit(10)
            self.log_signal.emit("=== 开始发布商品 ===\n")
            
            self.log_signal.emit("正在上传图片...")
            image_file = self.template_config.get("image", "")
            image_url = ""
            
            if image_file:
                image_path = os.path.join(self.template_dir, image_file)
                if os.path.exists(image_path):
                    image_url = self.upload_image(image_path)
                    self.log_signal.emit(f"图片上传成功: {image_url[:50]}...")
                else:
                    self.log_signal.emit(f"图片文件不存在: {image_path}")
            
            self.progress_signal.emit(50)
            
            default_config = self.config.get("default", {})
            product = default_config.copy()
            product.update(self.template_config)
            product["image"] = image_url
            product["slider_image"] = [image_url] if image_url else []
            
            self.log_signal.emit("正在发布商品...")
            result = self.add_product(product)
            
            self.progress_signal.emit(100)
            
            if result.get("status") == 200:
                self.log_signal.emit("\n✅ 发布成功!")
                self.finished_signal.emit(True, "发布成功!")
            else:
                msg = result.get("msg", "未知错误")
                self.log_signal.emit(f"\n❌ 发布失败: {msg}")
                self.finished_signal.emit(False, msg)
                
        except Exception as e:
            self.log_signal.emit(f"\n❌ 错误: {str(e)}")
            self.finished_signal.emit(False, str(e))

    def upload_image(self, file_path):
        BASE_URL = self.config.get("api", {}).get("base_url", "https://ed.weeeg.com/adminapi")
        url = f"{BASE_URL}/file/upload"
        headers = {
            "authori-zation": f"Bearer {self.token}",
            "Referer": self.config.get("api", {}).get("referer", "https://ed.weeeg.com/ekadmin/product/add_product")
        }
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'pid': ''}
            r = requests.post(url, headers=headers, files=files, data=data)
        
        if r.json().get("status") == 200:
            return self.get_latest_image_url()
        return ""

    def get_latest_image_url(self):
        BASE_URL = self.config.get("api", {}).get("base_url", "https://ed.weeeg.com/adminapi")
        url = f"{BASE_URL}/file/file?limit=1"
        headers = {
            "authori-zation": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*"
        }
        r = requests.get(url, headers=headers)
        data = r.json()
        if data.get("status") == 200:
            images = data.get("data", {}).get("list", [])
            if images:
                return images[0].get("att_dir", "")
        return ""

    def add_product(self, product_data):
        BASE_URL = self.config.get("api", {}).get("base_url", "https://ed.weeeg.com/adminapi")
        url = f"{BASE_URL}/product/product_goods/0"
        headers = {
            "authori-zation": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Referer": self.config.get("api", {}).get("referer", "https://ed.weeeg.com/ekadmin/product/add_product")
        }
        r = requests.post(url, headers=headers, json=product_data)
        return r.json()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.load_config()

    def init_ui(self):
        self.setWindowTitle("易店自动发货工具")
        self.setMinimumSize(600, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("Token:"))
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("请输入Bearer Token")
        token_layout.addWidget(self.token_input)
        
        self.save_token_btn = QPushButton("保存Token")
        self.save_token_btn.clicked.connect(self.save_token)
        token_layout.addWidget(self.save_token_btn)
        
        layout.addLayout(token_layout)
        
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("选择模板:"))
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(200)
        template_layout.addWidget(self.template_combo)
        
        self.refresh_btn = QPushButton("刷新模板")
        self.refresh_btn.clicked.connect(self.load_templates)
        template_layout.addWidget(self.refresh_btn)
        
        template_layout.addStretch()
        layout.addLayout(template_layout)
        
        self.publish_btn = QPushButton("开始发布")
        self.publish_btn.setMinimumHeight(40)
        self.publish_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.publish_btn.clicked.connect(self.start_publish)
        layout.addWidget(self.publish_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log_output)
        
        central_widget.setLayout(layout)

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self.config = json.load(f)
                token = self.config.get("token", "")
                if token and token != "请在此处填入你的Bearer Token":
                    self.token_input.setText(token)
        else:
            self.config = {}
        
        self.load_templates()

    def save_token(self):
        """保存Token到配置文件"""
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "警告", "请输入Token")
            return
        
        if not self.config:
            self.config = {
                "api": {
                    "base_url": "https://ed.weeeg.com/adminapi",
                    "referer": "https://ed.weeeg.com/ekadmin/product/add_product"
                },
                "default": {
                    "cate_id": [42],
                    "address": [1, 35, 408],
                    "logistics": ["1"],
                    "freight": 1,
                    "postage": 0,
                    "nick": ["ayekalooter"],
                    "unit_name": "件",
                    "is_show": 1
                }
            }
        
        self.config["token"] = token
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        QMessageBox.information(self, "成功", "Token已保存!")
        self.log("Token已保存到 config.json")

    def load_templates(self):
        """加载模板列表"""
        self.template_combo.clear()
        
        templates_dir = os.path.join(BASE_DIR, "templates")
        if not os.path.exists(templates_dir):
            self.log("templates 文件夹不存在，请先运行一次生成配置")
            return
        
        templates = [d for d in os.listdir(templates_dir) 
                   if os.path.isdir(os.path.join(templates_dir, d))]
        
        if templates:
            self.template_combo.addItems(templates)
            self.log(f"找到 {len(templates)} 个模板")
        else:
            self.log("没有找到模板")

    def start_publish(self):
        """开始发布"""
        token = self.token_input.text().strip()
        if not token or token == "请在此处填入你的Bearer Token":
            QMessageBox.warning(self, "警告", "请先配置Token")
            return
        
        template_name = self.template_combo.currentText()
        if not template_name:
            QMessageBox.warning(self, "警告", "请选择模板")
            return
        
        self.save_token()
        
        template_dir = os.path.join(BASE_DIR, "templates", template_name)
        config_path = os.path.join(template_dir, "config.json")
        
        if not os.path.exists(config_path):
            QMessageBox.critical(self, "错误", f"模板配置文件不存在: {config_path}")
            return
        
        with open(config_path, "r", encoding="utf-8") as f:
            template_config = json.load(f)
        
        self.log(f"选择模板: {template_name}")
        self.log(f"商品名称: {template_config.get('store_name')}")
        self.log(f"商品价格: {template_config.get('price')}")
        
        self.publish_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        self.worker = Worker(token, self.config, template_name, template_dir, template_config)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.publish_finished)
        self.worker.start()

    def publish_finished(self, success, message):
        """发布完成"""
        self.publish_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.critical(self, "失败", message)

    def log(self, message):
        """输出日志"""
        self.log_output.append(message)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()