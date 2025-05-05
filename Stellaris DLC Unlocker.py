import os
import shutil
import psutil
import re
from datetime import datetime

# --- Удаление старых папок Paradox ---
def delete_folder(path):
    if os.path.exists(path) and os.path.isdir(path):
        try:
            shutil.rmtree(path)
            print(f"[✔] Удалено: {path}")
        except Exception as e:
            print(f"[!] Ошибка при удалении {path}: {e}")
    else:
        print(f"[i] Папка не найдена или это не папка: {path}")

# --- Поиск установщика ---
def find_file(root_path, filename):
    for root, dirs, files in os.walk(root_path):
        if filename in files:
            return os.path.join(root, filename)
    return None

def get_available_drives():
    drives = []
    partitions = psutil.disk_partitions()
    for partition in partitions:
        if partition.fstype:
            drives.append(partition.mountpoint)
    return drives

def find_and_run_installer(filename):
    drives = get_available_drives()
    for drive in drives:
        print(f"[🔍] Ищу на диске: {drive}")
        file_path = find_file(drive, filename)
        if file_path:
            print(f"[✔] Файл найден: {file_path}")
            try:
                os.startfile(file_path)
                print(f"[▶] Установщик запущен.")
                return True
            except Exception as e:
                print(f"[!] Не удалось запустить установщик: {e}")
                return False
    print(f"[✖] Файл {filename} не найден на доступных дисках.")
    return False

def ask_user_about_update_cmd():
    while True:
        answer = input("\n🔧 Проверьте лаунчер. Требуется ли обновление? (да/нет): ").strip().lower()
        if answer in ['да', 'д', 'yes', 'y']:
            input("⏳ Обновите лаунчер и нажмите Enter, когда закончите...")
            break
        elif answer in ['нет', 'н', 'no', 'n']:
            print("▶ Обновление не требуется.")
            break
        else:
            print("❗ Пожалуйста, введите 'да' или 'нет'.")

# --- Копирование файлов в greenworks\lib ---
def update_launcher_files():
    base_path = os.path.join(os.environ['LOCALAPPDATA'], r"Programs\Paradox Interactive\launcher")
    pattern = re.compile(r'^launcher-v2\.(\d{4})\.(\d{1,2})$')

    latest_folder = None
    latest_date = None

    for folder in os.listdir(base_path):
        match = pattern.match(folder)
        if match:
            try:
                year = int(match.group(1))
                month = int(match.group(2))
                if 1 <= month <= 12:
                    folder_date = datetime(year, month, 1)
                    if latest_date is None or folder_date > latest_date:
                        latest_date = folder_date
                        latest_folder = folder
            except ValueError:
                continue

    if latest_folder:
        latest_path = os.path.join(base_path, latest_folder)
        final_path = os.path.join(latest_path, r"resources\app.asar.unpacked\node_modules\greenworks\lib")
        current_script_directory = os.path.dirname(os.path.abspath(__file__))
        source_folder = os.path.join(current_script_directory, "launcher")

        if os.path.exists(source_folder):
            files_copied = 0
            for file_name in os.listdir(source_folder):
                source_file = os.path.join(source_folder, file_name)
                dest_file = os.path.join(final_path, file_name)
                if os.path.isfile(source_file):
                    print(f"Копирование файла: {file_name}...")
                    shutil.copy2(source_file, dest_file)
                    files_copied += 1
            if files_copied > 0:
                print(f"\n{files_copied} файлов успешно перекинуты в папку '{final_path}'.")
            else:
                print("Нет файлов для копирования.")
        else:
            print(f"Папка с файлами {source_folder} не найдена.")
    else:
        print("Не найдены папки с нужным форматом 'launcher-v2.YYYY.M'.")

# --- Поиск Steam и копирование DLC и game ---
def find_steamapps_path():
    drives = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    print("🔍 Поиск папки Steam 'steamapps'...")
    for drive in drives:
        print(f"🔎 Проверка диска {drive}...")
        for root, dirs, files in os.walk(drive):
            if os.path.basename(root).lower() == "steamapps":
                print(f"📁 Найдена папка steamapps: {root}")
                return root
    print("❌ Папка steamapps не найдена.")
    return None

def copy_all_contents(src, dst):
    copied = 0
    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)
        if os.path.isdir(src_path):
            if os.path.exists(dst_path):
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
            print(f"📁 Папка скопирована: {item}")
            copied += 1
        elif os.path.isfile(src_path):
            shutil.copy2(src_path, dst_path)
            print(f"📄 Файл скопирован: {item}")
            copied += 1
    return copied

def copy_stellaris_files():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    steamapps_path = find_steamapps_path()

    if steamapps_path:
        stellaris_root = os.path.join(steamapps_path, "common", "Stellaris")
        stellaris_dlc = os.path.join(stellaris_root, "dlc")

        local_dlc = os.path.join(current_dir, "dlc")
        local_game = os.path.join(current_dir, "game")

        if os.path.exists(stellaris_dlc) and os.path.exists(local_dlc):
            print(f"\n🚀 Копирование содержимого из: {local_dlc} → {stellaris_dlc}\n")
            total_dlc = copy_all_contents(local_dlc, stellaris_dlc)
            print(f"\n✅ В папку DLC скопировано: {total_dlc} объектов")
        else:
            print("\n❌ Не удалось скопировать в DLC. Убедитесь, что существует папка 'dlc' рядом со скриптом и Stellaris установлен.")

        if os.path.exists(stellaris_root) and os.path.exists(local_game):
            print(f"\n🚀 Копирование содержимого из: {local_game} → {stellaris_root}\n")
            total_game = copy_all_contents(local_game, stellaris_root)
            print(f"\n✅ В корень Stellaris скопировано: {total_game} объектов")
        else:
            print("\n❌ Не удалось скопировать в папку Stellaris. Убедитесь, что рядом со скриптом есть папка 'game' и Stellaris установлен.")
    else:
        print("\n❌ Путь до Steamapps не найден.")

# --- Основная функция ---
def main():
    print("▶ Удаление старых папок Paradox...")
    user_profile = os.environ.get("USERPROFILE")
    folders_to_delete = [
        os.path.join(user_profile, r"AppData\Local\Programs\Paradox Interactive"),
        os.path.join(user_profile, r"AppData\Roaming\Paradox Interactive"),
        os.path.join(user_profile, r"AppData\Roaming\paradox-launcher-v2")
    ]

    for folder in folders_to_delete:
        print(f"\nУдаление: {folder}")
        delete_folder(folder)

    print("\n▶ Поиск установщика...")
    installer_filename = "launcher-installer-windows_2024.14.msi"
    if find_and_run_installer(installer_filename):
        ask_user_about_update_cmd()
        update_launcher_files()
        print("\n🔁 Переход к копированию в Stellaris...\n")
        copy_stellaris_files()
    else:
        print("⛔ Установщик не найден. Программа завершена.")
        return

    print("\n✅ Все этапы завершены! Можете закрывать файл. Удачной игры!")

if __name__ == "__main__":
    main()
