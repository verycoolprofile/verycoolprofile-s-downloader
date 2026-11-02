import sys
import os
import json
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import threading
import pystray
from PIL import Image, ImageDraw
import win32gui
import win32con
import tkinter as tk
import time
import winsound

# REQUIRES pip install flask flask-cors yt-dlp pystray pillow pywin32

# --- КОНФИГУРАЦИЯ И ПУТИ ---
if getattr(sys, 'frozen', False):
    APPLICATION_PATH = os.path.dirname(sys.executable)
else:
    APPLICATION_PATH = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(APPLICATION_PATH, "config.json")
DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads")
FFMPEG_LOCATION = ""
LANG = "RU"  # Язык по умолчанию

# --- СЛОВАРИ ПЕРЕВОДОВ ---
TRANSLATIONS = {
    "RU": {
        "title": " 🚀 VERYCOOLPROFILE'S DOWNLOADER - НАСТРОЙКА",
        "current_app": " Текущая папка с программой:",
        "current_ffmpeg": " Текущий путь к FFmpeg:",
        "not_installed": "НЕ УСТАНОВЛЕН",
        "status": " Статус FFmpeg:",
        "found": "✅ НАЙДЕН",
        "not_found": "❌ НЕ НАЙДЕН",
        "opt1": " 1. Указать путь к папке с ffmpeg.exe вручную",
        "opt2": " 2. Попробовать найти ffmpeg.exe автоматически",
        "opt3": " 3. Запустить сервер (нужен установленный FFmpeg)",
        "opt4": " 4. Swap languages (ENG/RU)",
        "enter_choice": " Введите цифру (1, 2, 3 или 4): ",
        "enter_path": "\n[ВВОД] Введите полный путь к папке, где лежит ffmpeg.exe",
        "example_path": r"Пример: D:\ffmpeg\bin",
        "path_prompt": "Путь: ",
        "saved_enter": "\n[УСПЕХ] Путь сохранен! Нажмите Enter...",
        "err_not_found_path": "\n[ОШИБКА] ffmpeg.exe не найден по этому пути. Нажмите Enter...",
        "searching": "\n[ИНФО] Идет поиск ffmpeg.exe в системе...",
        "auto_found": "\n[УСПЕХ] FFmpeg найден и путь сохранен: {}",
        "auto_not_found": "\n[ОШИБКА] Не удалось найти ffmpeg автоматически.\nСкачайте его и распакуйте, или укажите путь вручную (пункт 1).",
        "press_enter": "Нажмите Enter...",
        "err_not_configured": "\n[ОШИБКА] FFmpeg не настроен или не найден! Выберите пункт 1 или 2.",
        "starting": "\n[ЗАПУСК] Все в порядке. Запускаем сервер...",
        "err_invalid_choice": "\n[ОШИБКА] Неверный ввод. Введите 1, 2, 3 или 4.",
        "file_deleted": "\n[ВНИМАНИЕ] Файл ffmpeg.exe был перемещен или удален! Конфигурация сброшена.",
        "server_ready": "\n✅ Сервер успешно запущен на порту 5000.",
        "server_tray": "Свернуть в трей можно крестиком или через меню трея.",
        "notif_title": "verycoolprofile's downloader",
        "notif_msg": "File was downloaded successfully"
    },
    "ENG": {
        "title": " 🚀 VERYCOOLPROFILE'S DOWNLOADER - SETUP",
        "current_app": " Current application folder:",
        "current_ffmpeg": " Current FFmpeg path:",
        "not_installed": "NOT INSTALLED",
        "status": " FFmpeg Status:",
        "found": "✅ FOUND",
        "not_found": "❌ NOT FOUND",
        "opt1": " 1. Specify path to ffmpeg.exe manually",
        "opt2": " 2. Try to find ffmpeg.exe automatically",
        "opt3": " 3. Start server (requires installed FFmpeg)",
        "opt4": " 4. Swap languages (ENG/RU)",
        "enter_choice": " Enter number (1, 2, 3 or 4): ",
        "enter_path": "\n[INPUT] Enter full path to the folder containing ffmpeg.exe",
        "example_path": r"Example: D:\ffmpeg\bin",
        "path_prompt": "Path: ",
        "saved_enter": "\n[SUCCESS] Path saved! Press Enter...",
        "err_not_found_path": "\n[ERROR] ffmpeg.exe not found at this path. Press Enter...",
        "searching": "\n[INFO] Searching for ffmpeg.exe in the system...",
        "auto_found": "\n[SUCCESS] FFmpeg found and path saved: {}",
        "auto_not_found": "\n[ERROR] Could not find ffmpeg automatically.\nDownload it and extract, or specify the path manually (option 1).",
        "press_enter": "Press Enter...",
        "err_not_configured": "\n[ERROR] FFmpeg is not configured or not found! Choose option 1 or 2.",
        "starting": "\n[STARTING] All good. Starting server...",
        "err_invalid_choice": "\n[ERROR] Invalid input. Enter 1, 2, 3 or 4.",
        "file_deleted": "\n[WARNING] ffmpeg.exe was moved or deleted! Configuration reset.",
        "server_ready": "\n✅ Server successfully started on port 5000.",
        "server_tray": "You can hide to tray using the X button or tray menu.",
        "notif_title": "verycoolprofile's downloader",
        "notif_msg": "File was downloaded successfully"
    }
}


def t(key):
    """Возвращает перевод по ключу для текущего языка"""
    return TRANSLATIONS[LANG].get(key, key)


# --- РАБОТА С КОНФИГУРАЦИЕЙ ---
def load_config():
    global FFMPEG_LOCATION, LANG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                FFMPEG_LOCATION = config.get("ffmpeg_location", "")
                LANG = config.get("lang", "RU")
        except:
            pass


def save_config():
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({"ffmpeg_location": FFMPEG_LOCATION, "lang": LANG}, f)


def check_ffmpeg(path):
    """Проверяет, есть ли ffmpeg.exe по указанному пути"""
    if not path:
        return False
    return os.path.exists(os.path.join(path, "ffmpeg.exe"))


# --- АВТОПОИСК FFMPEG ---
def find_ffmpeg_auto():
    print(t("searching"))

    local_path = os.path.join(APPLICATION_PATH, "ffmpeg", "bin", "ffmpeg.exe")
    if os.path.exists(local_path):
        return os.path.dirname(local_path)

    try:
        result = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True, check=True)
        return os.path.dirname(result.stdout.strip().split('\n')[0])
    except:
        pass

    standard_paths = [r"C:\ffmpeg\bin", r"C:\Program Files\ffmpeg\bin", r"D:\ffmpeg\bin"]
    for path in standard_paths:
        if os.path.exists(os.path.join(path, "ffmpeg.exe")):
            return path

    return None


# --- МЕНЮ ---
def setup_menu():
    global FFMPEG_LOCATION, LANG
    load_config()

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')

        # ПРОВЕРКА: если путь сохранен, но файла нет - сбрасываем
        if FFMPEG_LOCATION and not check_ffmpeg(FFMPEG_LOCATION):
            print(t("file_deleted"))
            FFMPEG_LOCATION = ""
            save_config()
            time.sleep(2)
            continue

        print("=" * 60)
        print(t("title"))
        print("=" * 60)
        print(f"{t('current_app')} {APPLICATION_PATH}")
        print(f"{t('current_ffmpeg')} {FFMPEG_LOCATION if FFMPEG_LOCATION else t('not_installed')}")

        if FFMPEG_LOCATION and check_ffmpeg(FFMPEG_LOCATION):
            print(f"{t('status')} {t('found')}")
        else:
            print(f"{t('status')} {t('not_found')}")

        print("=" * 60)
        print(t("opt1"))
        print(t("opt2"))
        print(t("opt3"))
        print(t("opt4"))  # Пункт смены языка всегда на англ.
        print("=" * 60)

        choice = input(t("enter_choice")).strip()

        if choice == '1':
            print(t("enter_path"))
            print(t("example_path"))
            new_path = input(t("path_prompt")).strip().strip('"\'')
            if check_ffmpeg(new_path):
                FFMPEG_LOCATION = new_path
                save_config()
                print(t("saved_enter"))
                input()
            else:
                print(t("err_not_found_path"))
                input()

        elif choice == '2':
            found_path = find_ffmpeg_auto()
            if found_path:
                FFMPEG_LOCATION = found_path
                save_config()
                print(t("auto_found").format(found_path))
                input(t("press_enter"))
            else:
                print(t("auto_not_found"))
                input(t("press_enter"))

        elif choice == '3':
            if not FFMPEG_LOCATION or not check_ffmpeg(FFMPEG_LOCATION):
                print(t("err_not_configured"))
                input(t("press_enter"))
                continue
            print(t("starting"))
            time.sleep(1)
            break

        elif choice == '4':
            # Меняем язык и сохраняем
            LANG = "ENG" if LANG == "RU" else "RU"
            save_config()

        else:
            print(t("err_invalid_choice"))
            time.sleep(1)


# --- ОСНОВНОЙ КОД СЕРВЕРА ---
app = Flask(__name__)
CORS(app)

console_hwnd = None
tray_icon = None
is_hidden = False


def show_custom_notification(title, message):
    def _show():
        try:
            winsound.PlaySound("SystemNotification", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except:
            pass

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.configure(bg="#0a0a0a")

        screen_width = root.winfo_screenwidth()
        win_width = 320
        win_height = 95
        final_x = screen_width - win_width - 20
        start_x = screen_width + 10
        y = 50

        root.geometry(f"{win_width}x{win_height}+{start_x}+{y}")

        main_frame = tk.Frame(root, bg="#1a1a1a", highlightbackground="#333333", highlightthickness=1)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        red_stripe = tk.Frame(main_frame, bg="#ff0000", width=6)
        red_stripe.pack(side=tk.LEFT, fill=tk.Y)

        content_frame = tk.Frame(main_frame, bg="#1a1a1a")
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        text_frame = tk.Frame(content_frame, bg="#1a1a1a")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(12, 0))

        tk.Label(text_frame, text=title, fg="#ffffff", bg="#1a1a1a",
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(fill=tk.X)

        tk.Label(text_frame, text=message, fg="#aaaaaa", bg="#1a1a1a",
                 font=("Segoe UI", 9), anchor="w", justify=tk.LEFT).pack(fill=tk.X, pady=(3, 0))

        progress_bg = tk.Frame(content_frame, bg="#333333", height=4)
        progress_bg.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
        progress_bg.pack_propagate(False)

        progress_bar = tk.Frame(progress_bg, bg="#ff0000", height=4)
        progress_bar.place(x=0, y=0, relwidth=1, relheight=1)

        for widget in (root, main_frame, red_stripe, content_frame, text_frame, progress_bg):
            widget.bind("<Button-1>", lambda e: root.destroy())

        duration = 5000
        animation_speed = 15
        total_frames = duration // animation_speed

        current_x = start_x
        current_progress = 1.0
        state = "slide_in"

        def animate():
            nonlocal current_x, current_progress, state

            if state == "slide_in":
                current_x -= (start_x - final_x) / 15
                if current_x <= final_x:
                    current_x = final_x
                    state = "waiting"
                root.geometry(f"{win_width}x{win_height}+{int(current_x)}+{y}")
                root.after(animation_speed, animate)

            elif state == "waiting":
                current_progress -= (1.0 / total_frames)
                if current_progress <= 0:
                    current_progress = 0
                    state = "slide_out"
                progress_bar.place(relwidth=current_progress)
                root.after(animation_speed, animate)

            elif state == "slide_out":
                current_x += (start_x - final_x) / 15
                if current_x >= start_x:
                    root.destroy()
                    return
                root.geometry(f"{win_width}x{win_height}+{int(current_x)}+{y}")
                root.after(animation_speed, animate)

        root.after(50, animate)
        root.mainloop()

    threading.Thread(target=_show, daemon=True).start()


def download_task(url, media_type, quality):
    if '&list=' in url: url = url.split('&list=')[0]
    if '?list=' in url: url = url.split('?list=')[0]

    try:
        print(f"--- Starting download: {url} ---")

        ydl_opts = {
            'ffmpeg_location': FFMPEG_LOCATION,
            'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s.%(ext)s'),
            'noplaylist': True,
        }

        if media_type == 'mp3':
            bitrate = quality if quality in ['128', '192', '320'] else '192'
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': bitrate
                }]
            })
        else:
            ydl_opts.update({
                'format': f'bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/best[ext=mp4][height<={quality}]/best[height<={quality}]',
                'merge_output_format': 'mp4'
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print("--- Download finished successfully ---")
        show_custom_notification(t("notif_title"), t("notif_msg"))

    except Exception as e:
        print(f"Error in download_task: {e}")


def create_tray_image():
    image = Image.new('RGB', (64, 64), color='#0a0a0a')
    dc = ImageDraw.Draw(image)
    dc.rectangle((16, 16, 48, 48), fill='#ff0000')
    return image


def show_console(icon, item):
    global is_hidden, console_hwnd
    if console_hwnd:
        win32gui.ShowWindow(console_hwnd, win32con.SW_SHOW)
        win32gui.SetForegroundWindow(console_hwnd)
        is_hidden = False


def hide_console(icon, item):
    global is_hidden, console_hwnd
    if console_hwnd:
        win32gui.ShowWindow(console_hwnd, win32con.SW_HIDE)
        is_hidden = True


def quit_app(icon, item):
    global tray_icon
    if tray_icon:
        tray_icon.stop()
    os._exit(0)


def setup_tray():
    global tray_icon
    menu = pystray.Menu(
        pystray.MenuItem('Show Console', show_console, default=True),
        pystray.MenuItem('Hide', hide_console),
        pystray.MenuItem('Quit', quit_app)
    )
    tray_icon = pystray.Icon("FlaskDownloader", icon=create_tray_image(), title="Flask Downloader", menu=menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()


@app.route('/download', methods=['POST'])
def download():
    data = request.json
    threading.Thread(
        target=download_task,
        args=(data['url'], data['type'], data.get('quality', 'recommended'))
    ).start()
    return jsonify({"status": "started"})


@app.route('/hide', methods=['POST'])
def hide_window():
    global console_hwnd
    if console_hwnd:
        win32gui.ShowWindow(console_hwnd, win32con.SW_HIDE)
    return jsonify({"status": "hidden"})


if __name__ == '__main__':
    # 1. Запускаем меню настройки
    setup_menu()

    # 2. Настраиваем окно и трей
    console_hwnd = win32gui.GetForegroundWindow()
    setup_tray()

    print(t("server_ready"))
    print(t("server_tray"))

    # 3. Запускаем Flask в фоне
    threading.Thread(target=lambda: app.run(port=5000, use_reloader=False), daemon=True).start()

    # 4. Держим программу активной
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        os._exit(0)
