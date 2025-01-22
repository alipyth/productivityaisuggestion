import sys
import os
import time
import threading
from langchain_community.chat_models.ollama import ChatOllama

from datetime import datetime
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QTextEdit, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QLabel
import win32gui
import qdarkstyle


class ActivityMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window settings
        self.setWindowTitle("Modern Activity Monitor")
        self.setGeometry(200, 200, 600, 550)

        # Variables
        self.monitoring = False
        self.log_file_path = os.path.join(os.getcwd(), "activity_log.txt")
        self.api_key = None
        self.selected_model = None
        self.analysis_method = "OpenAI"  # Default method

        # Layout and widgets
        self.init_ui()

        # Thread for monitoring
        self.monitor_thread = None

    def init_ui(self):
        # Main layout
        layout = QVBoxLayout()
        # بعد از تعریف layout
        developer_info_layout = QHBoxLayout()

        # ایجاد QLabel برای نمایش اطلاعات توسعه‌دهنده
        developer_info_label = QLabel(self)
        developer_info_label.setText(
            '<a href="https://jahaniwww.com" style="color: white;">Developed By : Ali Jahani</a> | '
            '<a href="https://jahaniwww.com" style="color: white;">https://jahaniwww.com</a> | '
            '<a href="https://t.me/tarfandoonchannel" style="color: white;">Telegram Channel</a>'
        )
        developer_info_label.setOpenExternalLinks(True)
        developer_info_label.setAlignment(Qt.AlignCenter)

        # اضافه کردن به layout
        developer_info_layout.addWidget(developer_info_label)
        layout.addLayout(developer_info_layout)

        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel(f"Log File: {self.log_file_path}", self)
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)

        self.select_file_btn = QPushButton("Select Log File", self)
        self.select_file_btn.clicked.connect(self.select_log_file)
        file_layout.addWidget(self.select_file_btn)
        layout.addLayout(file_layout)

        # Method selection (OpenAI or Ollama)
        method_layout = QHBoxLayout()
        self.openai_radio = QRadioButton("OpenAI", self)
        self.ollama_radio = QRadioButton("Ollama", self)
        self.openai_radio.setChecked(True)
        self.analysis_method_group = QButtonGroup(self)
        self.analysis_method_group.addButton(self.openai_radio)
        self.analysis_method_group.addButton(self.ollama_radio)
        self.openai_radio.toggled.connect(self.update_analysis_method)
        self.ollama_radio.toggled.connect(self.update_analysis_method)

        method_layout.addWidget(QLabel("Select Analysis Method:"))
        method_layout.addWidget(self.openai_radio)
        method_layout.addWidget(self.ollama_radio)
        layout.addLayout(method_layout)

        # OpenAI API key and model input
        self.api_input = QLineEdit(self)
        self.api_input.setPlaceholderText("Enter OpenAI API Key")
        layout.addWidget(self.api_input)

        self.openai_model_input = QLineEdit(self)
        self.openai_model_input.setPlaceholderText("Enter OpenAI Model Name")
        layout.addWidget(self.openai_model_input)

        # Ollama model input
        self.ollama_model_input = QLineEdit(self)
        self.ollama_model_input.setPlaceholderText("Enter Ollama Model Name")
        layout.addWidget(self.ollama_model_input)

        # Start/Stop buttons
        self.start_btn = QPushButton("Start Monitoring", self)
        self.start_btn.setStyleSheet("background-color: green; color: white;")
        self.start_btn.clicked.connect(self.start_monitoring)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Monitoring", self)
        self.stop_btn.setStyleSheet("background-color: red; color: white;")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        # Status label
        self.status_label = QLabel("Status: Stopped", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Analyze log file
        self.analyze_btn = QPushButton("Analyze Log File", self)
        self.analyze_btn.clicked.connect(self.analyze_log)
        layout.addWidget(self.analyze_btn)

        self.result_area = QTextEdit(self)
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        # Set layout in a central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Initial visibility
        self.update_analysis_method()

    def update_analysis_method(self):
        """Update UI based on the selected analysis method."""
        if self.openai_radio.isChecked():
            self.analysis_method = "OpenAI"
            self.api_input.setVisible(True)
            self.openai_model_input.setVisible(True)
            self.ollama_model_input.setVisible(False)
        elif self.ollama_radio.isChecked():
            self.analysis_method = "Ollama"
            self.api_input.setVisible(False)
            self.openai_model_input.setVisible(False)
            self.ollama_model_input.setVisible(True)

    def select_log_file(self):
        # Open file dialog to select the log file
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Log File", self.log_file_path, "Text Files (*.txt);;All Files (*)", options=options
        )
        if file_path:
            self.log_file_path = file_path
            self.file_label.setText(f"Log File: {self.log_file_path}")

    def start_monitoring(self):
        if self.monitoring:
            return

        self.monitoring = True
        self.status_label.setText("Status: Running")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(target=self.monitor_activity, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.monitoring = False
        self.status_label.setText("Status: Stopped")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def monitor_activity(self):
        last_window = None

        while self.monitoring:
            try:
                current_window = win32gui.GetWindowText(win32gui.GetForegroundWindow())
                if current_window != last_window:
                    self.log_to_file(f"Active Window Changed: {current_window}")
                    last_window = current_window
                time.sleep(1)
            except Exception as e:
                self.log_to_file(f"Error: {e}")
                break

    def log_to_file(self, data):
        with open(self.log_file_path, "a", encoding="utf-8") as file:
            file.write(f"{datetime.now()}: {data}\n")

    def analyze_log(self):
        if not os.path.exists(self.log_file_path):
            self.result_area.setText("Log file not found!")
            return

        with open(self.log_file_path, "r", encoding="utf-8") as file:
            log_data = file.read()

        if self.analysis_method == "OpenAI":
            self.analyze_with_openai(log_data)
        elif self.analysis_method == "Ollama":
            self.analyze_with_ollama(log_data)

    def analyze_with_openai(self, log_data):
        self.api_key = self.api_input.text()
        model_name = self.openai_model_input.text()

        if not self.api_key or not model_name:
            self.result_area.setText("OpenAI API key or model name is missing!")
            return

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "این لاگ فعالیت های منه ، بهم بگو که چه میزان زمان روی چه کارهایی صرف کردم و پیشنهاداتی برای بهره وری بیشتر بهم بگو به زبان فارسی "},
                    {"role": "user", "content": log_data},
                ],
            )
            translated_text = response.choices[0].message.content.strip()
            self.result_area.setText(translated_text)
        except Exception as e:
            self.result_area.setText(f"Error: {e}")

    def analyze_with_ollama(self, log_data):
        # Get the selected model from input
        self.selected_model = self.ollama_model_input.text()

        if not self.selected_model:
            self.result_area.setText("Ollama model is missing!")
            return

        try:
            # Create an instance of the ChatOllama model with the selected model
            model = ChatOllama(model=self.selected_model)

            # Invoke the model with the log data (prompt)
            response = model.invoke(f"این لاگ فعالیت های منه ، بهم بگو که چه میزان زمان روی چه کارهایی صرف کردم و پیشنهاداتی برای بهره وری بیشتر بهم بگو به زبان فارسی:\n{log_data}")

            # Get the analysis result as a string (instead of printing it in the terminal)
            analysis_result = response.content

            # Display the result in the result_area widget
            self.result_area.setText(analysis_result)

        except Exception as e:
            # If any error occurs, show it in the result_area widget
            self.result_area.setText(f"Error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = ActivityMonitorApp()
    window.show()
    sys.exit(app.exec_())
