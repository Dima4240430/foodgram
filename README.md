# Foodgram
## Описание
Foodfram - веб-сервис для любителей вкусно покушать. Вы сможете делиться рецептами с фотографиями, добавлять к ним ингриденты, а также посмотреть, сохранить в избранном рецепты и скачать список необходимых продуктов для приготовления

## Технологии:
HTML, CSS, JavaScript, Python, Django, React, Docker.

### Клонирование
Клонируйте репозиторий
```
git clone git@github.com:Dima4240430/foodgram.git
```
### Подготовка виртуального окружения
Создаем окружения для проекта
```
sudo nano .env
```
```
POSTGRES_DB=********
POSTGRES_USER=********
POSTGRES_PASSWORD=********
DB_NAME=********

DB_HOST=db
DB_PORT=5432

SECRET_KEY='SECRET_KEY'
DEBUG = 'True'
ALLOWED_HOSTS = '127.0.0.1'
```

***Как зупустить проект на вашем сервере***

На вашем сервере создайте папку проекта.
Скопируйте в нее с локального компьютера файл infra/nginx.conf .env и docker-compose.production.yml

Выполните последовательно команды ниже, чтобы создать миграции, собрать статику, переместить ее в ожидаемую директорию и наполнить БД подготовленными данными.
Перед заполнением БД:
 откройте файл настроек вашего Django проекта settings.py и определите настройку CSV_DIR:
 CSV_DIR = BASE_DIR / 'csv_files'  # Замените 'csv_files' на фактическое имя каталога.
```
docker compose -f docker-compose.production.yml up
sudo docker compose -f docker-compose.production.yml exec backend python manage.py makemigrations
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/static/. /code/static/
sudo docker compose -f docker-compose.production.yml exec -ti backend python manage.py data_csv
sudo docker compose -f docker-compose.production.yml exec python manage.py tags
```
Перед заполнением БД

 Откройте файл настроек вашего Django проекта settings.py и определите настройку CSV_DIR:
 CSV_DIR = BASE_DIR / 'csv_files'  # Замените 'csv_files' на фактическое имя каталога.

```
## Статус
![Workflow Status](https://github.com/Dima4240430/foodgram/actions/workflows/main.yml/badge.svg)

**Развернутный проект доступен по сдресу [foodgramius.ddns.net](https://bumfa-foodgram.duckdns.org)**

## Администратор сайта
```
Электронная почта: admin@admin.ru
Имя пользователя: admin
Имя: admin
Фамилия: admin
Пароль: Dimka424
```

## Автор
Дмитрий Давыдов