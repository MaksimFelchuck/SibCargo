#!/bin/bash
# Скрипт для работы с миграциями Alembic

case "$1" in
  create)
    echo "Создание новой миграции..."
    docker-compose exec bot alembic revision --autogenerate -m "$2"
    ;;
  upgrade)
    echo "Применение миграций..."
    docker-compose exec bot alembic upgrade head
    ;;
  downgrade)
    echo "Откат последней миграции..."
    docker-compose exec bot alembic downgrade -1
    ;;
  current)
    echo "Текущая версия БД:"
    docker-compose exec bot alembic current
    ;;
  history)
    echo "История миграций:"
    docker-compose exec bot alembic history
    ;;
  *)
    echo "Использование: ./scripts/migrate.sh {create|upgrade|downgrade|current|history}"
    echo ""
    echo "Примеры:"
    echo "  ./scripts/migrate.sh create 'Add new field'"
    echo "  ./scripts/migrate.sh upgrade"
    echo "  ./scripts/migrate.sh current"
    exit 1
    ;;
esac

