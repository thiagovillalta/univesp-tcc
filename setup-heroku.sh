#!/bin/bash
# Script de configuração automática do Heroku para o SeniorGuard
# Configura PostgreSQL e Redis na aplicação Heroku

set -e

APP_NAME="${HEROKU_APP_NAME:-seniorguard}"

echo "========================================"
echo " Configuração do Heroku - SeniorGuard"
echo " App: $APP_NAME"
echo "========================================"
echo ""

# 1. Instalar PostgreSQL
echo "1. Instalando PostgreSQL (heroku-postgresql:mini)..."
if heroku addons:info heroku-postgresql -a "$APP_NAME" &>/dev/null; then
    echo "   PostgreSQL já está instalado."
else
    heroku addons:create heroku-postgresql:mini -a "$APP_NAME"
    echo "   PostgreSQL instalado com sucesso."
fi

# 2. Instalar Redis Cloud
echo ""
echo "2. Instalando Redis Cloud (rediscloud:30)..."
if heroku addons:info rediscloud -a "$APP_NAME" &>/dev/null; then
    echo "   Redis Cloud já está instalado."
else
    heroku addons:create rediscloud:30 -a "$APP_NAME"
    echo "   Redis Cloud instalado com sucesso."
fi

# 3. Verificar variáveis de ambiente
echo ""
echo "3. Verificando variáveis de ambiente..."
DATABASE_URL=$(heroku config:get DATABASE_URL -a "$APP_NAME" 2>/dev/null || true)
REDISCLOUD_URL=$(heroku config:get REDISCLOUD_URL -a "$APP_NAME" 2>/dev/null || true)

if [ -z "$DATABASE_URL" ]; then
    echo "   AVISO: DATABASE_URL não encontrada. Aguarde a provisão do PostgreSQL e tente novamente."
    exit 1
fi

if [ -z "$REDISCLOUD_URL" ]; then
    echo "   AVISO: REDISCLOUD_URL não encontrada. Aguarde a provisão do Redis e tente novamente."
    exit 1
fi

echo "   DATABASE_URL: configurada"
echo "   REDISCLOUD_URL: configurada"

# 4. Configurar DJANGO_SECRET_KEY se não existir
echo ""
echo "4. Verificando DJANGO_SECRET_KEY..."
SECRET_KEY=$(heroku config:get DJANGO_SECRET_KEY -a "$APP_NAME" 2>/dev/null || true)
if [ -z "$SECRET_KEY" ]; then
    echo "   Gerando nova SECRET_KEY..."
    NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))" 2>/dev/null || openssl rand -base64 48 | tr -d '\n=')
    heroku config:set DJANGO_SECRET_KEY="$NEW_SECRET" -a "$APP_NAME"
    echo "   DJANGO_SECRET_KEY configurada."
else
    echo "   DJANGO_SECRET_KEY já está configurada."
fi

# 5. Rodar migrations
echo ""
echo "5. Rodando migrations do banco de dados..."
heroku run python manage.py migrate --noinput -a "$APP_NAME"
echo "   Migrations aplicadas com sucesso."

# 6. Coletar arquivos estáticos
echo ""
echo "6. Coletando arquivos estáticos..."
heroku run python manage.py collectstatic --noinput --clear -a "$APP_NAME"
echo "   Arquivos estáticos coletados."

# 7. Reiniciar a aplicação
echo ""
echo "7. Reiniciando a aplicação..."
heroku restart -a "$APP_NAME"
echo "   Aplicação reiniciada."

# 8. Verificar status
echo ""
echo "8. Verificando status da aplicação..."
sleep 3
heroku ps -a "$APP_NAME"

echo ""
echo "========================================"
echo " Configuração concluída com sucesso!"
echo "========================================"
echo ""
echo "Para verificar os logs:"
echo "  heroku logs --tail -a $APP_NAME"
echo ""
echo "Para verificar os add-ons:"
echo "  heroku addons -a $APP_NAME"
echo ""
echo "URL da aplicação:"
echo "  https://$APP_NAME.herokuapp.com"
