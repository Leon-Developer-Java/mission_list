import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QListWidgetItem, QLineEdit, 
                             QTextEdit, QDialog, QLabel, QCheckBox, QSystemTrayIcon, 
                             QMenu, QAction, QMessageBox, QStyle)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
import sqlite3
from datetime import datetime

# 确保data目录存在
os.makedirs('data', exist_ok=True)

class Task:
    def __init__(self, id, title, description, completed=0, created_time=None, updated_time=None):
        self.id = id
        self.title = title
        self.description = description
        self.completed = completed
        self.created_time = created_time or datetime.now()
        self.updated_time = updated_time or datetime.now()

class TaskDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.task = task
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("添加任务" if not self.task else "编辑任务")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # 标题输入
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("任务标题:"))
        self.title_edit = QLineEdit()
        if self.task:
            self.title_edit.setText(self.task.title)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        
        # 描述输入
        layout.addWidget(QLabel("任务描述:"))
        self.desc_edit = QTextEdit()
        if self.task:
            self.desc_edit.setPlainText(self.task.description)
        layout.addWidget(self.desc_edit)
        
        # 按钮
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def get_data(self):
        return {
            'title': self.title_edit.text(),
            'description': self.desc_edit.toPlainText()
        }

class BatchAddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("批量添加任务")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("每行一个任务标题，可选添加描述(用|分隔):"))
        layout.addWidget(QLabel("例如: 购买食材|去超市买蔬菜水果"))
        
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)
        
        # 按钮
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("添加")
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def get_tasks(self):
        text = self.text_edit.toPlainText()
        tasks = []
        for line in text.split('\n'):
            if line.strip():
                parts = line.split('|', 1)
                title = parts[0].strip()
                desc = parts[1].strip() if len(parts) > 1 else ""
                if title:
                    tasks.append({'title': title, 'description': desc})
        return tasks

class SettingsDialog(QDialog):
    def __init__(self, parent=None, close_to_tray=True):
        super().__init__(parent)
        self.close_to_tray = close_to_tray
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("设置")
        self.setModal(True)
        layout = QVBoxLayout()
        
        self.tray_checkbox = QCheckBox("关闭时最小化到托盘")
        self.tray_checkbox.setChecked(self.close_to_tray)
        layout.addWidget(self.tray_checkbox)
        
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def get_settings(self):
        return {
            'close_to_tray': self.tray_checkbox.isChecked()
        }

class TaskItemWidget(QWidget):
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.initUI()
        
    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 移除原来的checkbox，只保留完成状态的勾选框
        self.completed_checkbox = QCheckBox()
        self.completed_checkbox.setChecked(bool(self.task.completed))
        self.completed_checkbox.toggled.connect(self.toggle_completed)
        layout.addWidget(self.completed_checkbox)
        
        # 任务信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        self.title_label = QLabel(self.task.title)
        self.title_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.title_label)
        
        if self.task.description:
            self.desc_label = QLabel(self.task.description)
            self.desc_label.setStyleSheet("color: gray; font-size: 12px;")
            info_layout.addWidget(self.desc_label)
        
        # 时间信息
        time_label = QLabel(self.task.created_time.strftime("%Y-%m-%d %H:%M"))
        time_label.setStyleSheet("color: gray; font-size: 10px;")
        info_layout.addWidget(time_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # 根据完成状态设置样式
        self.update_style()
        
    def toggle_completed(self, checked):
        self.task.completed = int(checked)
        # 更新数据库
        conn = sqlite3.connect('data/tasks.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET completed=?, updated_time=CURRENT_TIMESTAMP WHERE id=?', 
                      (int(checked), self.task.id))
        conn.commit()
        conn.close()
        
        # 更新样式
        self.update_style()
        
    def update_style(self):
        if self.task.completed:
            self.title_label.setStyleSheet("font-weight: bold; text-decoration: line-through; color: gray;")
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet("color: gray; font-size: 12px; text-decoration: line-through;")
        else:
            self.title_label.setStyleSheet("font-weight: bold;")
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet("color: gray; font-size: 12px; text-decoration: none;")

class TaskListApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_path = 'data/tasks.db'
        self.init_db()
        self.close_to_tray = True  # 默认关闭时最小化到托盘
        self.initUI()
        self.load_tasks()
        self.create_tray_icon()
        
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed INTEGER DEFAULT 0,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # 检查是否已存在completed字段，如果不存在则添加
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN completed INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass
        conn.commit()
        conn.close()
        
    def initUI(self):
        self.setWindowTitle('任务清单')
        self.setGeometry(100, 100, 600, 400)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton('添加任务')
        self.edit_btn = QPushButton('编辑任务')
        self.delete_btn = QPushButton('删除任务')
        self.batch_delete_btn = QPushButton('批量删除')
        self.batch_add_btn = QPushButton('批量添加')
        self.settings_btn = QPushButton('设置')
        
        self.add_btn.clicked.connect(self.add_task)
        self.edit_btn.clicked.connect(self.edit_task)
        self.delete_btn.clicked.connect(self.delete_task)
        self.batch_delete_btn.clicked.connect(self.batch_delete_tasks)
        self.batch_add_btn.clicked.connect(self.batch_add_tasks)
        self.settings_btn.clicked.connect(self.open_settings)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.batch_delete_btn)
        btn_layout.addWidget(self.batch_add_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.settings_btn)
        
        main_layout.addLayout(btn_layout)
        
        # 任务列表
        self.task_list = QListWidget()
        main_layout.addWidget(self.task_list)
        
    def load_tasks(self):
        self.task_list.clear()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, description, completed, created_time, updated_time FROM tasks ORDER BY created_time DESC')
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            task = Task(row[0], row[1], row[2], row[3],
                       datetime.fromisoformat(row[4]), 
                       datetime.fromisoformat(row[5]) if row[5] else datetime.fromisoformat(row[4]))
            self.add_task_to_list(task)
            
    def add_task_to_list(self, task):
        item = QListWidgetItem()
        widget = TaskItemWidget(task)
        item.setSizeHint(widget.sizeHint())
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, widget)
        # 将task对象关联到item上
        item.setData(Qt.UserRole, task)
        
    def add_task(self):
        dialog = TaskDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data['title'].strip():
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tasks (title, description, completed) 
                    VALUES (?, ?, ?)
                ''', (data['title'], data['description'], 0))  # 新任务默认未完成
                task_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                task = Task(task_id, data['title'], data['description'], 0)
                self.add_task_to_list(task)
                
    def edit_task(self):
        current_item = self.task_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "提示", "请先选择一个任务")
            return
            
        task = current_item.data(Qt.UserRole)
        dialog = TaskDialog(self, task)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data['title'].strip():
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tasks 
                    SET title=?, description=?, updated_time=CURRENT_TIMESTAMP 
                    WHERE id=?
                ''', (data['title'], data['description'], task.id))
                conn.commit()
                conn.close()
                
                # 更新界面
                task.title = data['title']
                task.description = data['description']
                task.updated_time = datetime.now()
                
                widget = self.task_list.itemWidget(current_item)
                widget.title_label.setText(task.title)
                if hasattr(widget, 'desc_label'):
                    widget.desc_label.setText(task.description)
                else:
                    if task.description:
                        widget.desc_label = QLabel(task.description)
                        widget.desc_label.setStyleSheet("color: gray; font-size: 12px;")
                        # 重新布局以添加描述标签
                        layout = widget.layout()
                        layout.insertWidget(1, widget.desc_label)
                # 更新样式（保持原有完成状态）
                widget.update_style()
                
    def delete_task(self):
        current_item = self.task_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "提示", "请先选择一个任务")
            return
            
        reply = QMessageBox.question(self, "确认", "确定要删除选中的任务吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            task = current_item.data(Qt.UserRole)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id=?', (task.id,))
            conn.commit()
            conn.close()
            
            # 从列表中移除
            row = self.task_list.row(current_item)
            self.task_list.takeItem(row)
            
    def batch_delete_tasks(self):
        selected_items = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            widget = self.task_list.itemWidget(item)
            # 使用完成状态的checkbox而不是旧的checkbox
            if widget.completed_checkbox.isChecked():
                selected_items.append(item)
                
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要删除的任务")
            return
            
        reply = QMessageBox.question(self, "确认", f"确定要删除选中的{len(selected_items)}个任务吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            ids_to_delete = []
            rows_to_remove = []
            
            for item in selected_items:
                task = item.data(Qt.UserRole)
                ids_to_delete.append(task.id)
                rows_to_remove.append(self.task_list.row(item))
                
            # 从数据库删除
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(ids_to_delete))
            cursor.execute(f'DELETE FROM tasks WHERE id IN ({placeholders})', ids_to_delete)
            conn.commit()
            conn.close()
            
            # 从列表中移除（从后往前删除，避免索引问题）
            for row in sorted(rows_to_remove, reverse=True):
                self.task_list.takeItem(row)
                
    def batch_add_tasks(self):
        dialog = BatchAddDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            tasks = dialog.get_tasks()
            if tasks:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                for task_data in tasks:
                    cursor.execute('''
                        INSERT INTO tasks (title, description, completed) 
                        VALUES (?, ?, ?)
                    ''', (task_data['title'], task_data['description'], 0))  # 新任务默认未完成
                    
                conn.commit()
                conn.close()
                
                # 重新加载任务列表
                self.load_tasks()
                QMessageBox.information(self, "提示", f"成功添加{len(tasks)}个任务")
                
    def open_settings(self):
        dialog = SettingsDialog(self, self.close_to_tray)
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            self.close_to_tray = settings['close_to_tray']
            
    def create_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
            
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))  # 使用标准图标
        
        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = QAction("显示主窗口", self)
        quit_action = QAction("退出", self)
        
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.quit_application)  # 使用新的退出方法
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # 连接系统托盘图标激活事件
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
    def on_tray_icon_activated(self, reason):
        """处理托盘图标点击事件"""
        if reason == QSystemTrayIcon.Trigger:  # 左键点击
            self.show()
            self.activateWindow()
            
    def closeEvent(self, event):
        # 检查系统托盘是否可用
        if self.close_to_tray and QSystemTrayIcon.isSystemTrayAvailable():
            # 显示提示信息
            QMessageBox.information(self, "提示", "程序将最小化到系统托盘，您可以通过托盘图标退出程序", QMessageBox.Ok)
            # 隐藏主窗口
            self.hide()
            # 忽略关闭事件，防止程序退出
            event.ignore()
        else:
            # 直接退出程序
            event.accept()
            
    def quit_application(self):
        """完全退出应用程序"""
        # 隐藏主窗口
        self.hide()
        # 隐藏系统托盘图标
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        # 退出应用
        QApplication.instance().quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 防止关闭主窗口时退出应用
    
    # 确保应用程序在所有窗口关闭后仍然运行
    window = TaskListApp()
    window.show()
    
    # 连接应用的aboutToQuit信号以确保正确清理
    app.aboutToQuit.connect(window.quit_application)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()