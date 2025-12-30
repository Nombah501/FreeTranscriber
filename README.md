# 🎙️ FreeTranscriber

**Ваш персональный ИИ-стенографист для Windows.**
Превращает голос в текст одним кликом. Быстро. Бесплатно. Приватно.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-2.0-purple.svg)

---

## 🚀 Что нового в версии 2.0

Мы полностью переработали управление программой! Теперь у вас есть полный контроль.

*   ⚙️ **Меню настроек:** Больше не нужно лезть в файлы конфигурации. Всё доступно через удобный интерфейс.
*   🎤 **Выбор микрофона:** Легко переключайтесь между гарнитурой, веб-камерой или студийным микрофоном.
*   🧠 **Управление ИИ:** Меняйте размер модели (от `tiny` до `large`) и язык распознавания прямо на лету.
*   ⚡ **Живой интерфейс:** Настройки прозрачности и поведения применяются мгновенно.

---

## 🎮 Как пользоваться

1.  **Начать запись:**
    *   Кликните левой кнопкой мыши по **круглой иконке**.
    *   Или нажмите горячие клавиши: `Ctrl + Shift + Space` (настраивается).
    *   *Индикатор станет красным.* 🔴

2.  **Закончить запись:**
    *   Кликните еще раз.
    *   *Индикатор станет оранжевым (обработка).* 🟠

3.  **Готово!**
    *   Текст автоматически появится в вашем редакторе/чате и скопируется в буфер обмена.
    *   *Индикатор мигнет зеленым.* 🟢

4.  **Настройки:**
    *   Нажмите **правой кнопкой мыши** на иконку.
    *   Выберите пункт **Settings**.
    *   Здесь можно изменить микрофон, модель AI, горячие клавиши и внешний вид.

5.  **Выход:**
    *   Нажмите правой кнопкой мыши на иконку приложения и выберите `Exit`.

## 📦 Установка

### Windows
1.  **Скачайте** архив с программой.
2.  **Распакуйте** его в любую папку.
3.  Запустите **`start.bat`**.

*Для скрытого запуска используйте `run_hidden.vbs`.*

### Linux (Arch/Manjaro/Ubuntu/Debian)

**Автоматическая установка:**
```bash
# Клонируйте репозиторий
git clone https://github.com/Nombah501/FreeTranscriber.git
cd FreeTranscriber

# Запустите скрипт установки
./install.sh
```

**Ручная установка:**
```bash
# Установите зависимости
pip3 install --user -r requirements.txt

# Установите приложение
pip3 install --user -e .

# Запустите мастер настройки
freetranscriber-setup
```

**Запуск:**
```bash
freetranscriber
```

**Автозапуск через systemd:**
```bash
mkdir -p ~/.config/systemd/user/
cp freetranscriber.service ~/.config/systemd/user/
systemctl --user enable --now freetranscriber.service
```

**Удаление:**
```bash
pip3 uninstall freetranscriber
rm ~/.local/share/applications/freetranscriber.desktop
systemctl --user disable --now freetranscriber.service
```

---
**Created with ❤️ by VibeCodding**
