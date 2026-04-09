# Guia de Configuração do Heroku - SeniorGuard

Este guia explica como configurar o **PostgreSQL** e o **Redis** na aplicação Heroku do SeniorGuard.

## Pré-requisitos

- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) instalado
- Acesso ao aplicativo `seniorguard` no Heroku
- Autenticado no Heroku CLI: `heroku login`

---

## Opção 1: Configuração Automática (Script)

Execute o script de configuração automática:

```bash
# Dar permissão de execução
chmod +x setup-heroku.sh

# Executar o script (usando o nome padrão "seniorguard")
./setup-heroku.sh

# Ou com um nome de app diferente
HEROKU_APP_NAME=meu-app ./setup-heroku.sh
```

O script faz automaticamente todos os passos descritos abaixo.

---

## Opção 2: Configuração Manual (Passo a Passo)

### Passo 1: Adicionar o PostgreSQL

```bash
# Instalar o add-on Heroku PostgreSQL (plano mini - gratuito)
heroku addons:create heroku-postgresql:mini -a seniorguard

# Verificar a instalação
heroku addons -a seniorguard

# Ver a URL do banco de dados (gerada automaticamente)
heroku config:get DATABASE_URL -a seniorguard
```

**O que acontece:** O Heroku cria um banco PostgreSQL e define automaticamente a variável de ambiente `DATABASE_URL`.

### Passo 2: Adicionar o Redis

```bash
# Instalar o add-on Redis Cloud (plano 30MB - gratuito)
heroku addons:create rediscloud:30 -a seniorguard

# Verificar a instalação
heroku addons -a seniorguard

# Ver a URL do Redis
heroku config:get REDISCLOUD_URL -a seniorguard
```

**O que acontece:** O Redis Cloud é provisionado e define a variável `REDISCLOUD_URL`, que já é lida pelo `settings.py`.

### Passo 3: Configurar a SECRET_KEY

```bash
# Gerar e definir uma SECRET_KEY segura
heroku config:set DJANGO_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')" -a seniorguard
```

**Por que é necessário:** Sem uma `SECRET_KEY` fixa, a chave muda a cada restart e invalida sessões/cookies.

### Passo 4: Aplicar as Migrations

```bash
# Criar as tabelas no banco PostgreSQL
heroku run python manage.py migrate --noinput -a seniorguard
```

**O que acontece:** Cria as tabelas `Device`, `SensorType`, `Sensor` e tabelas do Django (auth, sessions, etc.).

### Passo 5: Coletar Arquivos Estáticos

```bash
# Coletar CSS, imagens e outros arquivos estáticos
heroku run python manage.py collectstatic --noinput --clear -a seniorguard
```

**O que acontece:** O WhiteNoise serve os arquivos estáticos diretamente pelo Daphne, sem precisar de um servidor separado.

### Passo 6: Reiniciar a Aplicação

```bash
heroku restart -a seniorguard
```

### Passo 7: Verificar os Logs

```bash
heroku logs --tail -a seniorguard
```

---

## Verificação de Status

### Checar se tudo está funcionando

```bash
# Listar todos os add-ons
heroku addons -a seniorguard

# Verificar variáveis de ambiente
heroku config -a seniorguard

# Ver status dos dynos
heroku ps -a seniorguard

# Testar a conexão com o banco
heroku run python manage.py dbshell -a seniorguard
```

### Testar a Conexão com o Redis

```bash
heroku run python manage.py shell -a seniorguard
```

```python
# No console Python:
import os, redis
r = redis.from_url(os.environ["REDISCLOUD_URL"])
r.set("test", "ok")
print(r.get("test"))  # Deve imprimir b'ok'
```

### Verificar as Variáveis Necessárias

Após a configuração, `heroku config -a seniorguard` deve retornar:

```
DATABASE_URL:      postgres://...
REDISCLOUD_URL:    redis://...
DJANGO_SECRET_KEY: ...
```

---

## Troubleshooting

### Erro H10 - App Crashed

```bash
# Ver logs completos
heroku logs -n 200 -a seniorguard

# Causas comuns:
# 1. Migrations não rodadas → heroku run python manage.py migrate -a seniorguard
# 2. DATABASE_URL não definida → instalar o add-on PostgreSQL
# 3. SECRET_KEY ausente → heroku config:set DJANGO_SECRET_KEY="..." -a seniorguard
```

### Erro de Conexão com o Banco

```bash
# Verificar se o PostgreSQL está ativo
heroku pg:info -a seniorguard

# Checar a URL
heroku config:get DATABASE_URL -a seniorguard
```

### Erro de Conexão com o Redis

```bash
# Verificar se o Redis está ativo
heroku addons:info rediscloud -a seniorguard

# Checar a URL
heroku config:get REDISCLOUD_URL -a seniorguard
```

### WebSockets não funcionam

Verifique se o Procfile usa Daphne (não Gunicorn):

```
web: daphne -b 0.0.0.0 -p $PORT univesp_tcc.asgi:application
```

O Daphne suporta WebSockets e HTTP. O Gunicorn padrão não suporta WebSockets.

### Migrations com erro

```bash
# Ver o estado das migrations
heroku run python manage.py showmigrations -a seniorguard

# Forçar uma migration específica
heroku run python manage.py migrate seniorguard 0001 -a seniorguard
```

---

## Arquitetura da Aplicação

| Componente | Tecnologia | Uso |
|-----------|------------|-----|
| Servidor Web | Daphne (ASGI) | HTTP + WebSockets |
| Banco de Dados | PostgreSQL | Devices, Sensors, Auth |
| Cache/Mensagens | Redis (REDISCLOUD_URL) | Django Channels (WebSockets) |
| Arquivos Estáticos | WhiteNoise | CSS, imagens, JS |

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|---------|------------|-----------|
| `DATABASE_URL` | Sim | URL do PostgreSQL (definida pelo add-on) |
| `REDISCLOUD_URL` | Sim | URL do Redis (definida pelo add-on) |
| `DJANGO_SECRET_KEY` | Sim | Chave secreta do Django |
| `DYNO` | Auto | Definida pelo Heroku (detecta ambiente de produção) |
| `PGBOUNCER_URL` | Não | URL alternativa via PgBouncer (connection pooling) |
