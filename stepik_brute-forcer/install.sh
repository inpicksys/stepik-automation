# install.sh для Linux/Mac
#!/bin/bash
echo "Установка Stepik Brute Forcer Pro..."

# Создание директории
mkdir -p ~/stepik-brute-forcer
cd ~/stepik-brute-forcer

# Клонирование (если есть git репозиторий)
# git clone https://github.com/yourusername/stepik-brute-forcer.git .

# Или создание структуры
mkdir -p modules data logs

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install playwright cryptography

# Установка браузеров
playwright install firefox chromium

echo "Установка завершена!"
echo "Для запуска выполните: python main.py"