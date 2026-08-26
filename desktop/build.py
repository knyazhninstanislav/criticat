# build.py
import os
import shutil
import subprocess
import sys


def clean_build():
    """Очистка предыдущей сборки"""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Удалено: {dir_name}")

    files_to_remove = ['criticat.spec']
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"Удалено: {file_name}")


# def create_icon():
#     """Создание иконки"""
#     try:
#         from create_ico import generate_all_icons
#         generate_all_icons()
#         print("Иконка создана")
#     except Exception as e:
#         print(f"Ошибка создания иконки: {e}")


def install_requirements():
    """Установка зависимостей"""
    print("Установка зависимостей...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])


def build_exe():
    """Сборка exe файла"""
    print("Сборка exe файла...")
    subprocess.run([
        sys.executable, '-m', 'PyInstaller',
        '--onefile',  # Один файл
        '--windowed',  # Без консоли
        '--icon=criticat.ico',
        '--name=CritiCat',
        '--add-data=testbase;.',  # Для Windows
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=PySide6.QtWidgets',
        '--hidden-import=PySide6.QtSvg',
        '--hidden-import=requests',
        '--hidden-import=cryptography',
        'main.py'
    ])


def create_installer():
    """Создание установщика (требуется Inno Setup)"""
    iss_content = """
[Setup]
AppName=CritiCat
AppVersion=1.0.0
DefaultDirName={pf}\\CritiCat
DefaultGroupName=CritiCat
UninstallDisplayIcon={app}\\CritiCat.exe
OutputDir=installer
OutputBaseFilename=CritiCat_Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\\CritiCat.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "testbase"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\CritiCat"; Filename: "{app}\\CritiCat.exe"
Name: "{commondesktop}\\CritiCat"; Filename: "{app}\\CritiCat.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительно:"

[Run]
Filename: "{app}\\CritiCat.exe"; Description: "Запустить CritiCat"; Flags: nowait postinstall skipifsilent
"""

    with open('installer.iss', 'w', encoding='utf-8') as f:
        f.write(iss_content)

    print("Создан файл installer.iss для Inno Setup")
    print("Для создания установщика установите Inno Setup и скомпилируйте installer.iss")


def main():
    """Основная функция сборки"""
    print("=" * 50)
    print("Сборка CritiCat")
    print("=" * 50)

    # 1. Очистка
    print("\n1. Очистка предыдущей сборки...")
    clean_build()

    # # 2. Создание иконки
    # print("\n2. Создание иконки...")
    # create_icon()

    # 2. Установка зависимостей
    print("\n3. Установка зависимостей...")
    install_requirements()

    # 3. Сборка exe
    print("\n4. Сборка exe файла...")
    build_exe()

    # 4. Создание установщика
    print("\n5. Создание установщика...")
    create_installer()

    print("\n" + "=" * 50)
    print("Сборка завершена!")
    print("=" * 50)
    print(f"Exe файл: dist\\CritiCat.exe")
    print(f"Установщик: installer\\CritiCat_Setup.exe (если установлен Inno Setup)")


if __name__ == "__main__":
    main()