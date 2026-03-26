file := local.yml

up:
	docker compose -f ${file} up --remove-orphans

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

loaddata:
	docker compose -f ${file} run django python manage.py loaddata fixture.json
