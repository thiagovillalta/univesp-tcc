# univesp-tcc

## UNIVESP, 2026

Trabalho de Conclusão de Curso

### Comandos de instalação do python3:

`brew upgrade && brew update && brew install python3 && brew cleanup phyton3 && python3 --version`

### Comandos de instalação do django e demais componentes:

`pip install pip`

`pip install Django`

`pip install whitenoise`

`pip install dj-database-url`

`pip install django-heroku`

`pip install gunicorn`

`pip install daphne asgiref channels channels_redis`

`pip install qrcode --break-system-packages`

### Comandos de inicialização do projeto:

`pip freeze`

`django-admin startproject univesp_tcc`

`mv univesp_tcc univesp-tcc && cd univesp-tcc`

`django-admin startapp seniorguard`

### Comandos para execução do projeto localmente:

`cd univesp-tcc-main`

`python manage.py makemigrations`

`python manage.py migrate`

`python manage.py collectstatic --noinput --clear`

`python manage.py runserver 0.0.0.0:8000`

`daphne univesp_tcc.asgi:application --bind 127.0.0.1 --port 8000`

### Commandos para usar pool de conexões no Postgres

`heroku buildpacks:add https://github.com/heroku/heroku-buildpack-pgbouncer.git -a seniorguard`

`heroku buildpacks -a seniorguard`

O resultado deve ser:

`1. heroku/python`
`2. https://github.com/heroku/heroku-buildpack-pgbouncer.git`

Se estiver invertido, rode:

`heroku buildpacks:clear -a seniorguard`
`heroku buildpacks:add heroku/python -a seniorguard`
`heroku buildpacks:add https://github.com/heroku/heroku-buildpack-pgbouncer.git -a seniorguard`

### Comandos para configurar o pgbouncer buildpack:

`heroku config:set PGBouncer=true -a seniorguard`
`heroku config:set PGBOUNCER_POOL_MODE=session -a seniorguard`
`heroku config:set PGBOUNCER_DEFAULT_POOL_SIZE=20 -a seniorguard`
`heroku config:set PGBOUNCER_RESERVE_POOL_SIZE=5 -a seniorguard`

### Comandos para aplicar o pgbouncer buildpack

`git push heroku main`
`heroku restart -a seniorguard`

### Comandos para recriar o banco:

`cd univesp-tcc`

`find . -path "*/migrations/*.py" -not -name "__init__.py" -delete`

`find . -path "*/migrations/*.pyc" -delete`

`find . -path "*/db.sqlite3" -delete`

`python manage.py makemigrations`

`python manage.py migrate`

### Comandos para criar banco de dados na plataforma Heroku:

`heroku login`

`heroku run python manage.py makemigrations --app seniorguard`

`heroku run python manage.py migrate --app seniorguard`

### Comandos de debug na Heroku:

`heroku logs --tail --app seniorguard`

`heroku pg:psql --app seniorguard`

`SELECT * FROM seniorguard_sensor WHERE seniorguard_sensor.device_id = 'XX:XX:XX:XX:XX:XX' and seniorguard_sensor.sensor_type_id = 'rndA';`
