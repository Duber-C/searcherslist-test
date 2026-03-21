file := local.yml

up:
	docker compose -f ${file} up --remove-orphans

stop:
	docker compose -f ${file} stop

down:
	docker compose -f ${file} down

build:
	docker compose -f ${file} build

mm:
	docker compose -f ${file} run django python manage.py makemigrations

m:
	docker compose -f ${file} run django python manage.py migrate

admin:
	docker compose -f ${file} run django python manage.py createsuperuser

test:
	docker compose -f ${file} run django python manage.py test
