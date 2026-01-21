#!/usr/bin/env python3
"""
Главный файл приложения Stepik Brute Forcer Pro
"""
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from app_themed import StepikBruteForcerAppThemed
from PIL import Image, ImageTk
import os


def main():
    try:
        # Создаем тематическое окно
        root = ThemedTk(theme="plastik")  # Попробуйте: "arc", "clearlooks", "equilux", "plastik", "radiance"
        root.title("Stepik Brute Forcer Pro v3.0")

        # Устанавливаем иконку
        try:
            # Создаем простую иконку програмmatically
            icon = Image.new('RGB', (64, 64), color='#2e86c1')
            photo = ImageTk.PhotoImage(icon)
            root.iconphoto(True, photo)
        except:
            pass

        app = StepikBruteForcerAppThemed(root)

        # Центрирование окна
        root.update_idletasks()
        width = 1200
        height = 850
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')

        root.mainloop()
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()