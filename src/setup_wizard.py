import sys
import os
import subprocess
import grp
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication,
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QSpinBox,
    QButtonGroup,
    QRadioButton,
    QProgressBar,
    QGroupBox,
    QTextEdit,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
import sounddevice as sd

from core.config_manager import ConfigManager
from core.transcriber import Transcriber


class ModelDownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, model_size, device):
        super().__init__()
        self.model_size = model_size
        self.device = device

    def run(self):
        try:
            self.progress.emit(10)
            from faster_whisper import WhisperModel

            compute_type = "float16" if self.device == "cuda" else "int8"
            model = WhisperModel(
                self.model_size, device=self.device, compute_type=compute_type
            )

            self.progress.emit(100)
            self.finished.emit(
                True, f"Model '{self.model_size}' downloaded successfully!"
            )

            del model
        except Exception as e:
            self.finished.emit(False, f"Failed to download model: {e}")


class SystemCheck:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.display_server = self._detect_display_server()
        self.in_input_group = self._check_input_group()
        self.input_permissions = self._check_input_permissions()

    def _detect_display_server(self):
        try:
            if "WAYLAND_DISPLAY" in os.environ:
                return "wayland"
            elif "DISPLAY" in os.environ:
                return "x11"
            else:
                try:
                    result = subprocess.run(
                        [
                            "loginctl",
                            "show-session",
                            os.environ.get("XDG_SESSION_ID", "1"),
                            "-p",
                            "Type",
                        ],
                        capture_output=True,
                        text=True,
                    )
                    if "wayland" in result.stdout.lower():
                        return "wayland"
                except:
                    pass
            return "unknown"
        except:
            return "unknown"

    def _check_input_group(self):
        try:
            username = os.getlogin()
            groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
            if "input" in groups:
                return True
            gid = os.getgid()
            if grp.getgrgid(gid).gr_name == "input":
                return True
            return False
        except:
            return False

    def _check_input_permissions(self):
        try:
            input_files = ["/dev/input/event*", "/dev/input/mouse*", "/dev/input/kbd*"]
            import glob

            for pattern in input_files:
                for f in glob.glob(pattern):
                    try:
                        if os.access(f, os.R_OK):
                            return True
                    except:
                        continue
            return False
        except:
            return False

    def run_checks(self):
        issues = []
        warnings = []

        if self.display_server == "wayland":
            warnings.append(
                {
                    "title": "Обнаружен Wayland",
                    "message": "Горячие клавиши могут не работать на Wayland без дополнительных настроек.",
                    "solution": "Рекомендуется использовать X11 или добавить приложение в исключения Wayland.",
                }
            )

        if not self.in_input_group:
            issues.append(
                {
                    "title": "Нет доступа к группе input",
                    "message": "Пользователь не в группе input - горячие клавиши могут не работать.",
                    "solution": "Выполните команду: sudo usermod -a -G input $USER\nЗатем перезайдите в систему.",
                }
            )

        if not self.input_permissions:
            issues.append(
                {
                    "title": "Нет доступа к устройствам ввода",
                    "message": "Нет прав на чтение устройств ввода (/dev/input/*).",
                    "solution": "Добавьте пользователя в группу input: sudo usermod -a -G input $USER",
                }
            )

        self.issues = issues
        self.warnings = warnings
        return issues, warnings


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Добро пожаловать в FreeTranscriber")
        self.setSubTitle(
            "Превращает голос в текст одним кликом. Быстро. Бесплатно. Приватно."
        )

        layout = QVBoxLayout()

        welcome_text = QLabel(
            "<h2>🎙️ FreeTranscriber Setup</h2>"
            "<p>Этот мастер поможет вам настроить приложение:</p>"
            "<ul>"
            "<li>✅ Проверить систему</li>"
            "<li>✅ Выбрать модель ИИ для распознавания</li>"
            "<li>✅ Настроить горячие клавиши</li>"
            "<li>✅ Выбрать микрофон</li>"
            "<li>✅ Настроить поведение приложения</li>"
            "</ul>"
            "<p><b>Нажмите 'Далее' для начала настройки.</b></p>"
        )
        welcome_text.setWordWrap(True)
        welcome_text.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(welcome_text)
        layout.addStretch()

        self.setLayout(layout)


class SystemCheckPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Проверка системы")
        self.setSubTitle("Проверка совместимости с горячими клавишами")

        self.system_check = SystemCheck()

        layout = QVBoxLayout()

        self.checks_label = QLabel("Проверка...")
        self.checks_label.setWordWrap(True)
        layout.addWidget(self.checks_label)

        results_group = QGroupBox("Результаты проверки")
        results_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        self.hotkey_issue_check = QCheckBox(
            "Использовать только floating button (без горячих клавиш)"
        )
        self.hotkey_issue_check.setToolTip(
            "Отключите горячие клавиши, если есть проблемы с системой"
        )
        layout.addWidget(self.hotkey_issue_check)

        layout.addStretch()
        self.setLayout(layout)

        self.registerField("disable_hotkeys", self.hotkey_issue_check, "checked")

    def initializePage(self):
        issues, warnings = self.system_check.run_checks()

        display_server = self.system_check.display_server.upper()
        input_group = "✅ Да" if self.system_check.in_input_group else "❌ Нет"
        input_perm = "✅ Да" if self.system_check.input_permissions else "❌ Нет"

        results = (
            f"<b>Сервер отображения:</b> {display_server}<br><br>"
            f"<b>Группа input:</b> {input_group}<br>"
            f"<b>Доступ к устройствам:</b> {input_perm}<br><br>"
        )

        if warnings:
            results += "<b>⚠️ Предупреждения:</b><br>"
            for w in warnings:
                results += f"<br><b>{w['title']}</b><br>{w['message']}<br>"
                results += f"<i>Решение:</i> <span style='color: #888'>{w['solution']}</span><br>"

        if issues:
            results += "<br><b>❌ Проблемы:</b><br>"
            for i in issues:
                results += f"<br><b>{i['title']}</b><br>{i['message']}<br>"
                results += f"<i>Решение:</i> <span style='color: #888'>{i['solution']}</span><br>"

            self.hotkey_issue_check.setChecked(True)

        if not issues and not warnings:
            results += "✅ Система настроена корректно!"

        self.results_text.setHtml(results)

        if issues:
            self.checks_label.setText(
                "⚠️ Обнаружены проблемы - рекомендовано отключить горячие клавиши"
            )
            self.checks_label.setStyleSheet("color: #ff9800;")
        elif warnings:
            self.checks_label.setText(
                "⚠️ Есть предупреждения - горячие клавиши могут работать некорректно"
            )
            self.checks_label.setStyleSheet("color: #ffeb3b;")
        else:
            self.checks_label.setText("✅ Система готова к работе")
            self.checks_label.setStyleSheet("color: #4CAF50;")


class ModelPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Выбор модели ИИ")
        self.setSubTitle("Выберите модель для распознавания речи")

        layout = QVBoxLayout()

        info_label = QLabel(
            "<p><b>Выбор модели:</b></p>"
            "<ul>"
            "<li><b>tiny</b> - Самая быстрая (1GB), подходит для слабых ПК</li>"
            "<li><b>base</b> - Баланс скорости и точности (1.5GB), рекомендуемая</li>"
            "<li><b>small</b> - Хорошая точность (2GB)</li>"
            "<li><b>medium</b> - Высокая точность (5GB)</li>"
            "<li><b>large</b> - Максимальная точность (10GB)</li>"
            "</ul>"
        )
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info_label)

        layout.addWidget(QLabel("Размер модели:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.model_combo.setCurrentText("base")
        layout.addWidget(self.model_combo)

        layout.addWidget(QLabel("Устройство:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(["auto", "cpu", "cuda"])
        self.device_combo.setCurrentText("auto")
        layout.addWidget(self.device_combo)

        layout.addWidget(QLabel("Язык распознавания:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["ru", "en", "auto"])
        self.lang_combo.setCurrentText("ru")
        layout.addWidget(self.lang_combo)

        layout.addStretch()
        self.setLayout(layout)

        self.registerField("model_size", self.model_combo, "currentText")
        self.registerField("device", self.device_combo, "currentText")
        self.registerField("language", self.lang_combo, "currentText")

    def validatePage(self):
        model = self.model_combo.currentText()
        device = self.device_combo.currentText()

        if model == "large" and device == "cuda":
            confirm = self.wizard().confirm_large_model()
            if not confirm:
                return False
        return True


class AudioPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Настройка аудио")
        self.setSubTitle("Выберите устройство ввода и поведение")

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Микрофон:"))
        self.device_combo = QComboBox()
        self.populate_devices()
        layout.addWidget(self.device_combo)

        layout.addWidget(QLabel("Частота дискретизации:"))
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["16000", "44100", "48000"])
        self.sample_rate_combo.setCurrentText("16000")
        layout.addWidget(self.sample_rate_combo)

        layout.addStretch()
        self.setLayout(layout)

        self.registerField("input_device_id", self.device_combo, "currentData")
        self.registerField("sample_rate", self.sample_rate_combo, "currentText")

    def populate_devices(self):
        try:
            devices = sd.query_devices()
            self.device_combo.addItem("Системный по умолчанию", None)

            for i, dev in enumerate(devices):
                if dev["max_input_channels"] > 0:
                    name = f"{dev['name']} ({dev['hostapi']})"
                    self.device_combo.addItem(name, i)
        except Exception as e:
            print(f"Error getting devices: {e}")


class HotkeyPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Горячие клавиши")
        self.setSubTitle("Настройте горячую клавишу для записи")

        layout = QVBoxLayout()

        self.warning_label = QLabel()
        self.warning_label.setWordWrap(True)
        self.warning_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.warning_label)

        info_label = QLabel(
            "<p>Нажмите комбинацию клавиш для записи голоса.</p>"
            "<p>Примеры:</p>"
            "<ul>"
            "<li>ctrl+shift+space</li>"
            "<li>ctrl+alt+r</li>"
            "<li>ctrl+grave</li>"
            "</ul>"
        )
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info_label)

        self.hotkey_input = QLineEdit()
        self.hotkey_input.setText("ctrl+shift+space")
        self.hotkey_input.setPlaceholderText("Например: ctrl+shift+space")
        layout.addWidget(self.hotkey_input)

        layout.addStretch()
        self.setLayout(layout)

        self.registerField("hotkey", self.hotkey_input, "text")

    def initializePage(self):
        disabled = self.field("disable_hotkeys")

        if disabled:
            self.warning_label.setText(
                "<span style='color: #ff9800'>⚠️ Горячие клавиши отключены.</span><br>"
                "Вы выбрали использовать только floating кнопку."
            )
            self.hotkey_input.setEnabled(False)
        else:
            self.warning_label.setText("")
            self.hotkey_input.setEnabled(True)


class BehaviorPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Поведение приложения")
        self.setSubTitle("Настройте поведение при распознавании")

        layout = QVBoxLayout()

        self.top_check = QCheckBox("Всегда поверх других окон")
        self.top_check.setChecked(True)
        layout.addWidget(self.top_check)

        self.clipboard_check = QCheckBox("Копировать в буфер обмена")
        self.clipboard_check.setChecked(True)
        layout.addWidget(self.clipboard_check)

        self.type_check = QCheckBox("Вставлять текст в активное окно")
        self.type_check.setChecked(True)
        layout.addWidget(self.type_check)

        self.sounds_check = QCheckBox("Звуки уведомлений")
        self.sounds_check.setChecked(True)
        layout.addWidget(self.sounds_check)

        layout.addWidget(QLabel("Прозрачность иконки (покой):"))
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(10, 100)
        self.opacity_spin.setValue(60)
        self.opacity_spin.setSuffix("%")
        layout.addWidget(self.opacity_spin)

        layout.addStretch()
        self.setLayout(layout)

        self.registerField("always_on_top", self.top_check, "checked")
        self.registerField("copy_to_clipboard", self.clipboard_check, "checked")
        self.registerField("type_text", self.type_check, "checked")
        self.registerField("use_sounds", self.sounds_check, "checked")
        self.registerField("idle_opacity", self.opacity_spin, "value")


class DownloadPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Загрузка модели")
        self.setSubTitle("Модель будет загружена из интернета")

        layout = QVBoxLayout()

        info_label = QLabel(
            "Модель будет загружена один раз. Размер зависит от выбранной модели."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ожидание...")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.setLayout(layout)

        self.download_thread = None

    def initializePage(self):
        model_size = self.field("model_size")
        device = self.field("device")

        self.status_label.setText(f"Загрузка модели {model_size}...")
        self.progress_bar.setValue(0)

        self.download_thread = ModelDownloadThread(model_size, device)
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()

    def on_download_finished(self, success, message):
        if success:
            self.status_label.setText("✅ " + message)
            self.wizard().next()
        else:
            self.status_label.setText("❌ " + message)
            self.download_thread.wait()

    def isComplete(self):
        return self.status_label.text().startswith("✅")


class FinalPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Настройка завершена!")
        self.setSubTitle("FreeTranscriber готов к использованию")

        layout = QVBoxLayout()

        self.summary_text = QLabel()
        self.summary_text.setWordWrap(True)
        self.summary_text.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.summary_text)

        self.solutions_group = QGroupBox("Рекомендации")
        solutions_layout = QVBoxLayout()
        self.solutions_text = QTextEdit()
        self.solutions_text.setReadOnly(True)
        self.solutions_text.setMaximumHeight(150)
        solutions_layout.addWidget(self.solutions_text)
        self.solutions_group.setLayout(solutions_layout)
        self.solutions_group.setVisible(False)
        layout.addWidget(self.solutions_group)

        layout.addStretch()
        self.setLayout(layout)

    def initializePage(self):
        disable_hotkeys = self.field("disable_hotkeys")
        hotkey = self.field("hotkey") if not disable_hotkeys else "Отключены"
        always_on_top = "Включено" if self.field("always_on_top") else "Выключено"
        copy_to_clipboard = (
            "Включено" if self.field("copy_to_clipboard") else "Выключено"
        )

        summary = (
            "<h2>🎉 Успешно!</h2>"
            "<p>FreeTranscriber настроен и готов к работе.</p>"
            "<p><b>Настройки:</b></p>"
            "<ul>"
            f"<li>Модель: {self.field('model_size')}</li>"
            f"<li>Устройство: {self.field('device')}</li>"
            f"<li>Язык: {self.field('language')}</li>"
            f"<li>Горячие клавиши: {hotkey}</li>"
            f"<li>Поверх окон: {always_on_top}</li>"
            f"<li>Буфер обмена: {copy_to_clipboard}</li>"
            "</ul>"
        )

        system_check = self.wizard().system_check
        issues = system_check.issues
        warnings = system_check.warnings

        if issues or warnings:
            summary += "<p><b>⚠️ Обнаружены проблемы с системой:</b></p>"

            solutions = []
            for issue in issues:
                summary += f"<li style='color: #ff9800'>❌ {issue['title']}</li>"
                solutions.append(issue["solution"])
            for warning in warnings:
                summary += f"<li style='color: #ffeb3b'>⚠️ {warning['title']}</li>"
                solutions.append(warning["solution"])

            self.solutions_group.setVisible(True)
            self.solutions_text.setHtml(
                "<b>Для исправления проблем выполните:</b><br><br>"
                + "<br><br>".join(f"<code>{s}</code>" for s in solutions)
            )

        if disable_hotkeys:
            summary += "<p><b>ℹ️ Горячие клавиши отключены - используйте floating кнопку.</b></p>"

        summary += "<p><b>Как пользоваться:</b></p>"
        summary += "<ul>"
        summary += "<li>Кликните по иконке для записи</li>"
        if not disable_hotkeys:
            summary += "<li>Или используйте горячие клавиши</li>"
        summary += "<li>Текст автоматически вставится в активное окно</li>"
        summary += "</ul>"
        summary += "<p><b>Для изменения настроек:</b> ПКМ по иконке → Settings</p>"

        self.summary_text.setHtml(summary)


class SetupWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FreeTranscriber Setup")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QWizard {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWizardPage {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QComboBox, QLineEdit, QSpinBox {
                background: #333;
                color: #fff;
                border: 1px solid #555;
                padding: 6px;
                border-radius: 4px;
            }
            QCheckBox {
                color: #fff;
                spacing: 8px;
            }
            QPushButton {
                background: #555;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #666;
            }
            QWizard::wizard-button {
                background: #4CAF50;
            }
            QWizard::wizard-button:hover {
                background: #45a049;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 4px;
                background: #333;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #4CAF50;
            }
            QGroupBox {
                color: #fff;
                border: 1px solid #555;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTextEdit {
                background: #333;
                color: #fff;
                border: 1px solid #555;
                padding: 6px;
                border-radius: 4px;
            }
        """)

        self.system_check = SystemCheck()

        self.addPage(WelcomePage())
        self.addPage(SystemCheckPage())
        self.addPage(ModelPage())
        self.addPage(AudioPage())
        self.addPage(HotkeyPage())
        self.addPage(BehaviorPage())
        self.addPage(DownloadPage())
        self.addPage(FinalPage())

    def confirm_large_model(self):
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Модель 'large' занимает ~10GB и требует мощного оборудования.\nПродолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def accept(self):
        config = ConfigManager()

        config.set("model_size", self.field("model_size"))
        config.set("device", self.field("device"))
        config.set("language", self.field("language"))
        config.set("input_device_id", self.field("input_device_id"))
        config.set("sample_rate", int(self.field("sample_rate")))

        if self.field("disable_hotkeys"):
            config.set("hotkey", "")
            config.set("disable_hotkeys", True)
        else:
            config.set("hotkey", self.field("hotkey"))
            config.set("disable_hotkeys", False)

        config.set("always_on_top", self.field("always_on_top"))
        config.set("copy_to_clipboard", self.field("copy_to_clipboard"))
        config.set("type_text", self.field("type_text"))
        config.set("use_sounds", self.field("use_sounds"))
        config.set("idle_opacity", self.field("idle_opacity") / 100.0)

        print("Configuration saved successfully!")
        super().accept()


def run_setup():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    wizard = SetupWizard()
    wizard.show()

    result = wizard.exec()

    if result == QWizard.DialogCode.Accepted:
        print("Setup completed successfully!")
        return 0
    else:
        print("Setup cancelled.")
        return 1


def is_first_run():
    config = ConfigManager()
    return config.get("model_size") == "base"


if __name__ == "__main__":
    sys.exit(run_setup())
