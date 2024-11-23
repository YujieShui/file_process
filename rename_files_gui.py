import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QRadioButton, QButtonGroup, QFileDialog, QMessageBox,
                            QTextEdit)
from PyQt6.QtCore import Qt
from rename_files import rename_files
import sys
import io

class OutputRedirector(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.append(text.rstrip())

class RenameToolGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文件批量重命名工具")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # 创建主窗口部件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 标题
        title_label = QLabel("文件批量重命名工具")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建水平布局来放置控制面板和输出区域
        content_layout = QHBoxLayout()
        
        # 左侧控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # 文件夹选择部分
        folder_layout = QHBoxLayout()
        self.folder_path = QLineEdit()
        self.folder_path.setPlaceholderText("请选择要处理的文件夹")
        folder_button = QPushButton("浏览...")
        folder_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(QLabel("文件夹:"))
        folder_layout.addWidget(self.folder_path)
        folder_layout.addWidget(folder_button)
        control_layout.addLayout(folder_layout)
        
        # 重命名模式选择
        mode_group = QButtonGroup(self)
        self.prefix_radio = QRadioButton("删除[数字]前缀")
        self.replace_radio = QRadioButton("替换字符串")
        self.replace_radio.setChecked(True)
        mode_group.addButton(self.prefix_radio)
        mode_group.addButton(self.replace_radio)
        
        control_layout.addWidget(QLabel("重命名模式:"))
        control_layout.addWidget(self.prefix_radio)
        control_layout.addWidget(self.replace_radio)
        
        # 字符串替换部分
        old_layout = QHBoxLayout()
        self.old_pattern = QLineEdit()
        old_layout.addWidget(QLabel("要替换的字符串:"))
        old_layout.addWidget(self.old_pattern)
        control_layout.addLayout(old_layout)
        
        new_layout = QHBoxLayout()
        self.new_pattern = QLineEdit()
        new_layout.addWidget(QLabel("替换后的字符串:"))
        new_layout.addWidget(self.new_pattern)
        control_layout.addLayout(new_layout)
        
        # 按钮部分
        button_layout = QHBoxLayout()
        preview_button = QPushButton("预览更改")
        execute_button = QPushButton("执行重命名")
        preview_button.clicked.connect(lambda: self.rename_files(preview=True))
        execute_button.clicked.connect(lambda: self.rename_files(preview=False))
        button_layout.addWidget(preview_button)
        button_layout.addWidget(execute_button)
        control_layout.addLayout(button_layout)
        
        # 添加一些空白
        control_layout.addStretch()
        
        # 右侧输出区域
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        
        # 添加控制面板和输出区域到主布局
        content_layout.addWidget(control_panel)
        content_layout.addWidget(self.output_text)
        layout.addLayout(content_layout)
        
        # 重定向标准输出到文本框
        self.stdout_redirector = OutputRedirector(self.output_text)
        sys.stdout = self.stdout_redirector
    
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.folder_path.setText(folder)
    
    def rename_files(self, preview=True):
        # 清空输出区域
        self.output_text.clear()
        
        # 获取输入
        directory = self.folder_path.text()
        if not directory:
            QMessageBox.warning(self, "错误", "请选择要处理的文件夹！")
            return
        
        mode = 'prefix' if self.prefix_radio.isChecked() else 'replace'
        old_pattern = self.old_pattern.text() if mode == 'replace' else ''
        new_pattern = self.new_pattern.text() if mode == 'replace' else ''
        
        if mode == 'replace' and not old_pattern:
            QMessageBox.warning(self, "错误", "请输入要替换的字符串！")
            return
        
        # 调用重命名函数
        try:
            found_files = rename_files(directory, mode=mode, 
                                     old_pattern=old_pattern,
                                     new_pattern=new_pattern,
                                     preview=preview)
            
            if preview:
                if found_files > 0:
                    QMessageBox.information(self, "预览完成", 
                        "预览已完成，请查看右侧输出区域。\n如确认无误，可点击'执行重命名'进行实际重命名操作。")
                else:
                    QMessageBox.information(self, "预览完成", 
                        "未找到需要重命名的文件。")
            else:
                if found_files > 0:
                    QMessageBox.information(self, "重命名完成", 
                        f"成功重命名了 {found_files} 个文件！")
                else:
                    QMessageBox.information(self, "重命名完成", 
                        "未找到需要重命名的文件。")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"操作失败：{str(e)}")

def main():
    app = QApplication(sys.argv)
    window = RenameToolGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 