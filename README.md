Клонируйте репозиторий:
git clone https://github.com/Tinom14/Avito_test.git
cd avito_test

Создайте файл окружения .env:
cp .env.example .env

Отредактируйте .env файл:
SECRET_KEY=your_django_secret_key
POSTGRES_DB=avito_db
POSTGRES_USER=avito_user
POSTGRES_PASSWORD=strong_password
DJANGO_ALLOWED_HOSTS=localhost,web

Соберите и запустите контейнеры:
docker-compose up --build

Примените миграции:
docker-compose exec web python manage.py migrate

