import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QListWidgetItem, QLineEdit, 
                             QTextEdit, QDialog, QLabel, QCheckBox, QSystemTrayIcon, 
                             QMenu, QAction, QMessageBox, QStyle, QComboBox, QGroupBox, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
import sqlite3
from datetime import datetime

# 确保data目录存在
os.makedirs('data', exist_ok=True)

class Task:
    def __init__(self, id, title, description, category='未分类', priority=1, urgency=1, duration=2, completed=0, created_time=None, updated_time=None):
        self.id = id
        self.title = title
        self.description = description
        self.category = category
        self.priority = priority  # 1=低, 2=中, 3=高
        self.urgency = urgency    # 1=不急, 2=一般, 3=紧急
        self.duration = duration  # 1=短期, 2=中期, 3=长期
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
        self.resize(450, 400)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)  # 设置整体间距
        
        # 标题输入
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("任务标题:"))
        self.title_edit = QLineEdit()
        if self.task:
            self.title_edit.setText(self.task.title)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        
        # 分类选择
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("任务分类:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(['未分类', '工作', '个人', '学习', '家庭', '健康', '娱乐'])
        if self.task:
            index = self.category_combo.findText(self.task.category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        category_layout.addWidget(self.category_combo)
        layout.addLayout(category_layout)
        
        # 优先级选择
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("优先级:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['低', '中', '高'])
        if self.task:
            self.priority_combo.setCurrentIndex(self.task.priority - 1)
        priority_layout.addWidget(self.priority_combo)
        layout.addLayout(priority_layout)
        
        # 紧急程度选择
        urgency_layout = QHBoxLayout()
        urgency_layout.addWidget(QLabel("紧急程度:"))
        self.urgency_combo = QComboBox()
        self.urgency_combo.addItems(['不急', '一般', '紧急'])
        if self.task:
            self.urgency_combo.setCurrentIndex(self.task.urgency - 1)
        urgency_layout.addWidget(self.urgency_combo)
        layout.addLayout(urgency_layout)
        
        # 任务周期选择
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("任务周期:"))
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(['短期', '中期', '长期'])
        if self.task:
            self.duration_combo.setCurrentIndex(self.task.duration - 1)
        duration_layout.addWidget(self.duration_combo)
        layout.addLayout(duration_layout)
        
        # 描述输入
        layout.addWidget(QLabel("任务描述:"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        priority_map = {'低': 1, '中': 2, '高': 3}
        urgency_map = {'不急': 1, '一般': 2, '紧急': 3}
        duration_map = {'短期': 1, '中期': 2, '长期': 3}
        
        return {
            'title': self.title_edit.text(),
            'description': self.desc_edit.toPlainText(),
            'category': self.category_combo.currentText(),
            'priority': priority_map[self.priority_combo.currentText()],
            'urgency': urgency_map[self.urgency_combo.currentText()],
            'duration': duration_map[self.duration_combo.currentText()]
        }

class BatchAddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("批量添加任务")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("每行一个任务标题，可选添加描述(用|分隔):"))
        layout.addWidget(QLabel("例如: 购买食材|去超市买蔬菜水果"))
        
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)
        
        # 默认属性设置
        attr_group = QGroupBox("默认属性设置")
        attr_layout = QVBoxLayout()
        
        # 分类选择
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("默认分类:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(['未分类', '工作', '个人', '学习', '家庭', '健康', '娱乐'])
        category_layout.addWidget(self.category_combo)
        attr_layout.addLayout(category_layout)
        
        # 优先级选择
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("默认优先级:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['低', '中', '高'])
        priority_layout.addWidget(self.priority_combo)
        attr_layout.addLayout(priority_layout)
        
        # 紧急程度选择
        urgency_layout = QHBoxLayout()
        urgency_layout.addWidget(QLabel("默认紧急程度:"))
        self.urgency_combo = QComboBox()
        self.urgency_combo.addItems(['不急', '一般', '紧急'])
        urgency_layout.addWidget(self.urgency_combo)
        attr_layout.addLayout(urgency_layout)
        
        # 任务周期选择
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("默认任务周期:"))
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(['短期', '中期', '长期'])
        duration_layout.addWidget(self.duration_combo)
        attr_layout.addLayout(duration_layout)
        
        attr_group.setLayout(attr_layout)
        layout.addWidget(attr_group)
        
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
        
    def get_default_attributes(self):
        priority_map = {'低': 1, '中': 2, '高': 3}
        urgency_map = {'不急': 1, '一般': 2, '紧急': 3}
        duration_map = {'短期': 1, '中期': 2, '长期': 3}
        
        return {
            'category': self.category_combo.currentText(),
            'priority': priority_map[self.priority_combo.currentText()],
            'urgency': urgency_map[self.urgency_combo.currentText()],
            'duration': duration_map[self.duration_combo.currentText()]
        }

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
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)  # 增大间距
        
        # 主要信息行
        top_layout = QHBoxLayout()
        
        # 完成状态的勾选框
        self.completed_checkbox = QCheckBox()
        self.completed_checkbox.setChecked(bool(self.task.completed))
        self.completed_checkbox.toggled.connect(self.toggle_completed)
        top_layout.addWidget(self.completed_checkbox)
        
        # 任务标题
        self.title_label = QLabel(self.task.title)
        self.title_label.setStyleSheet("font-weight: bold;")
        self.title_label.setWordWrap(False)  # 不换行显示
        self.title_label.setMinimumWidth(100)  # 设置最小宽度
        self.title_label.setMaximumWidth(300)  # 设置最大宽度
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 允许扩展
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        
        # 标签区域（集中显示在右侧）
        tags_layout = QHBoxLayout()
        tags_layout.setSpacing(5)
        
        # 分类标签
        self.category_label = QLabel(f"[{self.task.category}]")
        self.category_label.setStyleSheet("color: blue; font-size: 10px; border: 1px solid blue; border-radius: 3px; padding: 1px 3px;")
        tags_layout.addWidget(self.category_label)
        
        # 优先级标签
        priority_text = ['低', '中', '高'][self.task.priority - 1]
        priority_color = ['green', 'orange', 'red'][self.task.priority - 1]
        self.priority_label = QLabel(priority_text)
        self.priority_label.setStyleSheet(f"color: {priority_color}; font-size: 10px; border: 1px solid {priority_color}; border-radius: 3px; padding: 1px 3px;")
        tags_layout.addWidget(self.priority_label)
        
        # 紧急程度标签
        urgency_text = ['不急', '一般', '紧急'][self.task.urgency - 1]
        urgency_color = ['gray', 'orange', 'red'][self.task.urgency - 1]
        self.urgency_label = QLabel(urgency_text)
        self.urgency_label.setStyleSheet(f"color: {urgency_color}; font-size: 10px; border: 1px solid {urgency_color}; border-radius: 3px; padding: 1px 3px;")
        tags_layout.addWidget(self.urgency_label)
        
        # 任务周期标签
        duration_text = ['短期', '中期', '长期'][self.task.duration - 1]
        self.duration_label = QLabel(duration_text)
        self.duration_label.setStyleSheet("color: purple; font-size: 10px; border: 1px solid purple; border-radius: 3px; padding: 1px 3px;")
        tags_layout.addWidget(self.duration_label)
        
        top_layout.addLayout(tags_layout)
        self.main_layout.addLayout(top_layout)
        
        # 任务描述（直接显示，不隐藏）
        if self.task.description:
            self.desc_label = QLabel(self.task.description)
            self.desc_label.setStyleSheet("color: gray; font-size: 12px; margin-left: 20px;")
            self.desc_label.setWordWrap(True)  # 允许描述换行
            self.main_layout.addWidget(self.desc_label)
        
        # 时间信息行
        time_layout = QHBoxLayout()
        time_label = QLabel(self.task.created_time.strftime("%Y-%m-%d %H:%M"))
        time_label.setStyleSheet("color: gray; font-size: 10px; margin-left: 20px;")
        time_layout.addWidget(time_label)
        time_layout.addStretch()
        self.main_layout.addLayout(time_layout)
        
        self.setLayout(self.main_layout)
        
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
        
        # 通知主窗口重新排序任务列表
        main_window = self.window()
        if hasattr(main_window, 'reorder_tasks'):
            main_window.reorder_tasks()
        
    def update_style(self):
        if self.task.completed:
            self.title_label.setStyleSheet("font-weight: bold; text-decoration: line-through; color: gray;")
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet("color: gray; font-size: 12px; text-decoration: line-through; margin-left: 20px;")
        else:
            self.title_label.setStyleSheet("font-weight: bold;")
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet("color: gray; font-size: 12px; margin-left: 20px;")
                
    def update_labels(self):
        """更新标签显示内容"""
        # 更新分类标签
        self.category_label.setText(f"[{self.task.category}]")
        
        # 更新优先级标签
        priority_text = ['低', '中', '高'][self.task.priority - 1]
        priority_color = ['green', 'orange', 'red'][self.task.priority - 1]
        self.priority_label.setText(priority_text)
        self.priority_label.setStyleSheet(f"color: {priority_color}; font-size: 10px; border: 1px solid {priority_color}; border-radius: 3px; padding: 1px 3px;")
        
        # 更新紧急程度标签
        urgency_text = ['不急', '一般', '紧急'][self.task.urgency - 1]
        urgency_color = ['gray', 'orange', 'red'][self.task.urgency - 1]
        self.urgency_label.setText(urgency_text)
        self.urgency_label.setStyleSheet(f"color: {urgency_color}; font-size: 10px; border: 1px solid {urgency_color}; border-radius: 3px; padding: 1px 3px;")
        
        # 更新任务周期标签
        duration_text = ['短期', '中期', '长期'][self.task.duration - 1]
        self.duration_label.setText(duration_text)
        self.duration_label.setStyleSheet("color: purple; font-size: 10px; border: 1px solid purple; border-radius: 3px; padding: 1px 3px;")
        
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
                category TEXT DEFAULT '未分类',
                priority INTEGER DEFAULT 1,  -- 1=低, 2=中, 3=高
                urgency INTEGER DEFAULT 1,   -- 1=不急, 2=一般, 3=紧急
                duration INTEGER DEFAULT 2,  -- 1=短期, 2=中期, 3=长期
                completed INTEGER DEFAULT 0,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # 检查并添加新字段
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN category TEXT DEFAULT "未分类"')
        except sqlite3.OperationalError:
            pass  # 字段已存在
            
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 1')
        except sqlite3.OperationalError:
            pass  # 字段已存在
            
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN urgency INTEGER DEFAULT 1')
        except sqlite3.OperationalError:
            pass  # 字段已存在
            
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN duration INTEGER DEFAULT 2')
        except sqlite3.OperationalError:
            pass  # 字段已存在
            
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
        # 按照紧急程度和任务周期排序：
        # 1. 紧急+短期 (urgency=3, duration=1)
        # 2. 紧急+中期 (urgency=3, duration=2)
        # 3. 紧急+长期 (urgency=3, duration=3)
        # 4. 一般+短期 (urgency=2, duration=1)
        # 5. 一般+中期 (urgency=2, duration=2)
        # 6. 一般+长期 (urgency=2, duration=3)
        # 7. 不急+短期 (urgency=1, duration=1)
        # 8. 不急+中期 (urgency=1, duration=2)
        # 9. 不急+长期 (urgency=1, duration=3)
        # 在每个 urgency+duration 组内，未完成的任务在前，已完成的任务在后，按创建时间倒序排列
        cursor.execute('''SELECT id, title, description, category, priority, urgency, duration, completed, created_time, updated_time 
                         FROM tasks ORDER BY 
                         (3 - urgency) * 3 + (duration - 1),  -- Urgency and duration sorting
                         completed ASC,  -- Uncompleted first, completed last
                         created_time DESC''')  # Sort by creation time descending
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            task = Task(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7],
                       datetime.fromisoformat(row[8]), 
                       datetime.fromisoformat(row[9]) if row[9] else datetime.fromisoformat(row[8]))
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
                    INSERT INTO tasks (title, description, category, priority, urgency, duration, completed) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (data['title'], data['description'], data['category'], data['priority'], 
                      data['urgency'], data['duration'], 0))  # 新任务默认未完成
                task_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                task = Task(task_id, data['title'], data['description'], data['category'], 
                           data['priority'], data['urgency'], data['duration'], 0)
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
                    SET title=?, description=?, category=?, priority=?, urgency=?, duration=?, updated_time=CURRENT_TIMESTAMP 
                    WHERE id=?
                ''', (data['title'], data['description'], data['category'], data['priority'], 
                      data['urgency'], data['duration'], task.id))
                conn.commit()
                conn.close()
                
                # 更新任务对象
                task.title = data['title']
                task.description = data['description']
                task.category = data['category']
                task.priority = data['priority']
                task.urgency = data['urgency']
                task.duration = data['duration']
                task.updated_time = datetime.now()
                
                # 更新界面
                widget = self.task_list.itemWidget(current_item)
                widget.title_label.setText(task.title)
                
                # 更新标签显示
                widget.task = task  # 更新widget中的task引用
                widget.update_labels()  # 刷新标签显示
                
                # 更新描述信息
                if hasattr(widget, 'desc_label'):
                    widget.desc_label.setText(task.description)
                    # 如果描述为空，隐藏描述标签
                    if not task.description:
                        widget.desc_label.hide()
                    else:
                        widget.desc_label.show()
                else:
                    # 如果之前没有描述，现在添加了描述
                    if task.description:
                        widget.desc_label = QLabel(task.description)
                        widget.desc_label.setStyleSheet("color: gray; font-size: 12px; margin-left: 20px;")
                        widget.desc_label.setWordWrap(True)
                        # 插入到正确位置
                        widget.main_layout.insertWidget(1, widget.desc_label)
                
                # 更新样式（保持原有完成状态）
                widget.update_style()
                
                # 重新加载任务列表以确保排序正确
                self.load_tasks()
                
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
            default_attrs = dialog.get_default_attributes()
            if tasks:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                for task_data in tasks:
                    cursor.execute('''
                        INSERT INTO tasks (title, description, category, priority, urgency, duration, completed) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (task_data['title'], task_data['description'], 
                          default_attrs['category'], default_attrs['priority'], 
                          default_attrs['urgency'], default_attrs['duration'], 0))  # 新任务默认未完成
                    
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
            
    def reorder_tasks(self):
        """重新排序任务列表，将已完成的任务移到底部"""
        self.load_tasks()
        
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
        # 检查系统托盘是否可用并且用户设置了最小化到托盘
        if self.close_to_tray and QSystemTrayIcon.isSystemTrayAvailable():
            # 显示提示信息
            QMessageBox.information(self, "提示", "程序将最小化到系统托盘，您可以通过托盘图标退出程序", QMessageBox.Ok)
            # 隐藏主窗口
            self.hide()
            # 忽略关闭事件，防止程序退出
            event.ignore()
        else:
            # 直接退出程序
            self.quit_application()
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