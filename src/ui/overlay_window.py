from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QAction
from .settings_dialog import SettingsDialog

class FloatingButton(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        
        # Connect config signals
        self.config.config_changed.connect(self.on_config_changed)
        
        self.update_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setFixedSize(60, 60)
        self.is_recording = False
        self.is_processing = False
        self.is_success = False
        
        self._drag_pos = QPoint()
        self._press_pos = QPoint()
        self._is_dragging = False
        
        # Load position
        x = self.config.get("window_x")
        y = self.config.get("window_y")
        self.move(x, y)
        
        # Idle opacity
        self.idle_opacity = self.config.get("idle_opacity")
        self.setWindowOpacity(self.idle_opacity)
        
        # Settings dialog instance
        self.settings_dialog = None

    def update_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.config.get("always_on_top"):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        
        # We need to hide/show to apply flag changes dynamically sometimes, 
        # but for staysOnTop usually simply setWindowFlags works if we re-show.
        was_visible = self.isVisible()
        self.setWindowFlags(flags)
        if was_visible:
            self.show()

    def on_config_changed(self, key, value):
        if key == "idle_opacity":
            self.idle_opacity = value
            if not self.underMouse() and not self.is_recording:
                self.setWindowOpacity(value)
        elif key == "always_on_top":
            self.update_flags()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #333; color: white; border: 1px solid #555; }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #555; }
        """)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close_application)
        menu.addAction(exit_action)
        
        menu.exec(event.globalPos())

    def open_settings(self):
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self.config, self)
        
        # Center settings relative to widget or screen
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def close_application(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._is_dragging = False
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            diff = (event.globalPosition().toPoint() - self._press_pos).manhattanLength()
            if diff > 5: # Threshold for drag
                self._is_dragging = True
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._is_dragging:
                self.clicked.emit()
            else:
                # Save new position after drag
                pos = self.pos()
                self.config.set("window_x", pos.x())
                self.config.set("window_y", pos.y())
                
            self._is_dragging = False
            event.accept()

    def enterEvent(self, event):
        self.setWindowOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_recording and not self.is_processing:
            self.setWindowOpacity(self.idle_opacity)
        super().leaveEvent(event)

    def set_recording(self, state):
        self.is_recording = state
        self.is_success = False
        self.is_processing = False
        self.setWindowOpacity(1.0 if state else self.idle_opacity)
        self.update()

    def set_processing(self, state):
        self.is_processing = state
        self.is_recording = False
        self.setWindowOpacity(1.0 if state else self.idle_opacity)
        self.update()

    def flash_success(self):
        self.is_success = True
        self.is_processing = False
        self.update()
        QTimer.singleShot(1500, self._reset_state)

    def _reset_state(self):
        self.is_success = False
        self.update()
        if not self.underMouse():
            self.setWindowOpacity(self.idle_opacity)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background circle
        if self.is_success:
             color = QColor(50, 200, 50)
        elif self.is_recording:
            color = QColor(200, 50, 50)
        elif self.is_processing:
            color = QColor(255, 165, 0)
        else:
            color = QColor(50, 50, 50)
            
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(5, 5, 50, 50)

        # Draw icons
        painter.setBrush(QColor(255, 255, 255))
        if self.is_recording:
            painter.drawRect(22, 22, 16, 16)
        elif self.is_processing:
             painter.drawEllipse(18, 28, 4, 4)
             painter.drawEllipse(28, 28, 4, 4)
             painter.drawEllipse(38, 28, 4, 4)
        elif self.is_success:
             pen = QPen(QColor(255, 255, 255), 3)
             painter.setPen(pen)
             painter.drawLine(18, 30, 26, 38)
             painter.drawLine(26, 38, 42, 22)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(22, 22, 16, 16)
