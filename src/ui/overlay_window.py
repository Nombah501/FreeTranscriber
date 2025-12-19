from PyQt6.QtWidgets import QWidget, QMenu, QApplication
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QAction
from .settings_dialog import SettingsDialog
import time
import sys
import ctypes

# ctypes.wintypes is only available on Windows
try:
    import ctypes.wintypes
except ImportError:
    pass

class FloatingButton(QWidget):
    clicked = pyqtSignal()
    native_hotkey_received = pyqtSignal(int) # Emits hotkey ID
    
    # UI Constants
    COLOR_SUCCESS = QColor(50, 200, 50)
    COLOR_ERROR = QColor(200, 50, 50)
    COLOR_LOADING = QColor(50, 50, 200)
    COLOR_PROCESSING = QColor(255, 165, 0)
    COLOR_IDLE = QColor(50, 50, 50)
    COLOR_ICON = QColor(255, 255, 255)

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
        self.is_error = False
        self.is_loading = False
        
        self._drag_pos = QPoint()
        self._press_pos = QPoint()
        self._is_dragging = False
        self._last_click_time = 0  # For rapid click protection

        # Load position with validation
        x = self.config.get("window_x")
        y = self.config.get("window_y")
        initial_pos = QPoint(x, y)

        # Validate position is on-screen, reset to default if off-screen
        validated_pos = self._constrain_to_screen(initial_pos)
        if validated_pos != initial_pos:
            # Position was off-screen, save corrected position
            self.config.set("window_x", validated_pos.x())
            self.config.set("window_y", validated_pos.y())

        self.move(validated_pos)
        
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

    def _constrain_to_screen(self, pos):
        """
        Ensures at least 20px of widget remains visible on screen.
        Returns constrained position within screen boundaries.
        If position is completely off-screen, returns center of primary screen.
        """
        screens = QApplication.screens()
        if not screens:
            # Fallback to default position
            return QPoint(100, 100)

        widget_rect = self.frameGeometry()
        widget_rect.moveTo(pos)

        # Minimum visible pixels required
        min_visible = 20

        # Check if widget is on any screen
        on_screen = False
        for screen in screens:
            screen_geom = screen.availableGeometry()
            if screen_geom.intersects(widget_rect):
                on_screen = True
                break

        if not on_screen:
            # Widget is completely off-screen, reset to center of primary screen
            primary_screen = QApplication.primaryScreen()
            screen_geom = primary_screen.availableGeometry()
            return QPoint(
                screen_geom.center().x() - self.width() // 2,
                screen_geom.center().y() - self.height() // 2
            )

        # Find the screen containing the widget center
        target_screen = None
        for screen in screens:
            if screen.availableGeometry().contains(widget_rect.center()):
                target_screen = screen
                break

        if not target_screen:
            # Use primary screen as fallback
            target_screen = QApplication.primaryScreen()

        screen_geom = target_screen.availableGeometry()

        # Constrain position to ensure minimum visibility
        x = pos.x()
        y = pos.y()

        # Left edge constraint
        if x < screen_geom.left() - self.width() + min_visible:
            x = screen_geom.left() - self.width() + min_visible

        # Right edge constraint
        if x > screen_geom.right() - min_visible:
            x = screen_geom.right() - min_visible

        # Top edge constraint
        if y < screen_geom.top() - self.height() + min_visible:
            y = screen_geom.top() - self.height() + min_visible

        # Bottom edge constraint
        if y > screen_geom.bottom() - min_visible:
            y = screen_geom.bottom() - min_visible

        return QPoint(x, y)

    def reset_position_to_default(self):
        """
        Resets widget position to center of primary screen.
        Called from Settings dialog "Reset Position" button.
        """
        primary_screen = QApplication.primaryScreen()
        screen_geom = primary_screen.availableGeometry()

        center_x = screen_geom.center().x() - self.width() // 2
        center_y = screen_geom.center().y() - self.height() // 2

        self.move(center_x, center_y)
        self.config.set("window_x", center_x)
        self.config.set("window_y", center_y)

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
                # Rapid click protection: 300ms debounce
                current_time = time.time()
                if current_time - self._last_click_time > 0.3:
                    self._last_click_time = current_time
                    self.clicked.emit()
            else:
                # Constrain position to screen boundaries
                pos = self._constrain_to_screen(self.pos())
                self.move(pos)

                # Save new position after drag
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

    def set_loading(self, state):
        self.is_loading = state
        self.is_processing = False # Loading overrides processing visual
        self.setWindowOpacity(1.0 if state else self.idle_opacity)
        self.update()

    def flash_success(self):
        self.is_success = True
        self.is_processing = False
        self.is_error = False
        self.update()
        QTimer.singleShot(1500, self._reset_state)

    def flash_error(self):
        self.is_error = True
        self.is_processing = False
        self.is_recording = False
        self.is_success = False
        self.update()
        QTimer.singleShot(1500, self._reset_state)

    def _reset_state(self):
        self.is_success = False
        self.is_error = False
        self.update()
        if not self.underMouse():
            self.setWindowOpacity(self.idle_opacity)

    def nativeEvent(self, eventType, message):
        """
        Handle Windows native events. Used for global hotkeys (WM_HOTKEY).
        """
        if sys.platform == "win32":
             # Robust check for wintypes presence
             try:
                 import ctypes.wintypes
                 if eventType == b"windows_generic_MSG" or eventType == "windows_generic_MSG":
                    msg = ctypes.wintypes.MSG.from_address(message.__int__())
                    if msg.message == 0x0312: # WM_HOTKEY
                        hotkey_id = msg.wParam
                        self.native_hotkey_received.emit(hotkey_id)
                        return True, 0
             except ImportError:
                 pass
        return super().nativeEvent(eventType, message)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background circle
        if self.is_success:
             color = self.COLOR_SUCCESS
        elif self.is_error:
             color = self.COLOR_ERROR
        elif self.is_loading:
             color = self.COLOR_LOADING
        elif self.is_recording:
            color = self.COLOR_ERROR
        elif self.is_processing:
            color = self.COLOR_PROCESSING
        else:
            color = self.COLOR_IDLE
            
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(5, 5, 50, 50)

        # Draw icons
        painter.setBrush(self.COLOR_ICON)
        if self.is_recording:
            painter.drawRect(22, 22, 16, 16)
        elif self.is_processing:
             painter.drawEllipse(18, 28, 4, 4)
             painter.drawEllipse(28, 28, 4, 4)
             painter.drawEllipse(38, 28, 4, 4)
        elif self.is_success:
             pen = QPen(self.COLOR_ICON, 3)
             painter.setPen(pen)
             painter.drawLine(18, 30, 26, 38)
             painter.drawLine(26, 38, 42, 22)
        elif self.is_error:
             pen = QPen(self.COLOR_ICON, 3)
             painter.setPen(pen)
             # Draw X
             painter.drawLine(20, 20, 40, 40)
             painter.drawLine(40, 20, 20, 40)
        elif self.is_loading:
             # Draw ...
             painter.setBrush(self.COLOR_ICON)
             painter.setPen(Qt.PenStyle.NoPen)
             painter.drawEllipse(15, 28, 4, 4)
             painter.drawEllipse(28, 28, 4, 4)
             painter.drawEllipse(41, 28, 4, 4)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(22, 22, 16, 16)
