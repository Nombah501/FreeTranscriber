from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen

class FloatingButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setFixedSize(60, 60)
        self.is_recording = False
        self._drag_pos = QPoint()
        
        # Idle opacity
        self.setWindowOpacity(0.7)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # If moved very little, treat as click
            self.clicked.emit()
            event.accept()

    def enterEvent(self, event):
        self.setWindowOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_recording:
            self.setWindowOpacity(0.7)
        super().leaveEvent(event)

    def set_recording(self, state):
        self.is_recording = state
        self.update() # Trigger repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background circle
        color = QColor(200, 50, 50) if self.is_recording else QColor(50, 50, 50)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(5, 5, 50, 50)

        # Draw icon (simple white circle for now)
        painter.setBrush(QColor(255, 255, 255))
        if self.is_recording:
            # Square icon for stop
            painter.drawRect(22, 22, 16, 16)
        else:
            # Circle for record
            painter.drawEllipse(22, 22, 16, 16)

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    btn = FloatingButton()
    btn.show()
    sys.exit(app.exec())
