from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QAction, QPainterPath

class FloatingButton(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
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