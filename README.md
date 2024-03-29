# Проект Yatube

### Описание
Портал с возможностью объединения пользователей в сообщества, публикации комментариев к постам, подписки на посты интересующих пользователей. Используется адаптивная верстка, пагинация постов и кэширование, верификация данных при регистрации, смена и восстановление пароля через почту. Написаны тесты для проверки работоспособности сервиса.

### Технологии
Python 3.8  
Django 2.2  
Bootstrap 5  
SQLite3   
Faker 

### Запуск проекта в dev-режиме:
- Установить и активировать виртуальное окружение
```
python3 -m venv env
source env/bin/activate
python3 -m pip install --upgrade pip
```

- Установить зависимости из файла requirements.txt
```
pip install -r requirements.txt
```

- Выполнить миграции
```
python3 manage.py migrate
```
 
- Запустить проект
```
python3 manage.py runserver
```
