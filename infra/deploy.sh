#!/usr/bin/env bash
# NavIS — deploy script
# Запуск: bash ~/navis/infra/deploy.sh
set -euo pipefail

COMPOSE="docker compose -f ~/navis/infra/docker-compose.yml"
MIGRATIONS_DIR="$(dirname "$0")/migrations"
APPLIED_FILE="$MIGRATIONS_DIR/.applied"

log() { echo "[deploy] $*"; }

# ─── 1. Git pull ──────────────────────────────────────────────────────────────
log "=== Git pull ==="
cd ~/navis

if ! git pull 2>/dev/null; then
    log "Конфликты локальных изменений — сбрасываем и тянем заново"
    git reset --hard HEAD
    git clean -fd
    git pull
fi

log "Код обновлён: $(git log -1 --oneline)"

# ─── 2. Миграции ──────────────────────────────────────────────────────────────
log "=== Миграции ==="
touch "$APPLIED_FILE"

for sql_file in $(ls "$MIGRATIONS_DIR"/*.sql 2>/dev/null | sort); do
    filename=$(basename "$sql_file")
    if grep -qx "$filename" "$APPLIED_FILE"; then
        log "  SKIP $filename (уже применена)"
    else
        log "  APPLY $filename ..."
        cat "$sql_file" | $COMPOSE exec -T postgres psql -U navis -d navis
        echo "$filename" >> "$APPLIED_FILE"
        log "  OK $filename"
    fi
done

# ─── 3. Пересборка контейнеров ────────────────────────────────────────────────
log "=== Build ==="
$COMPOSE build --no-cache backend frontend worker

log "=== Up ==="
$COMPOSE up -d

# ─── 4. Перезапуск nginx (обновить upstream IP после пересборки) ──────────────
log "=== Restart nginx ==="
sleep 3
$COMPOSE restart nginx

# ─── 5. Проверка ─────────────────────────────────────────────────────────────
log "=== Health check ==="
sleep 5
if curl -sf http://localhost/api/health > /dev/null; then
    log "OK — NavIS доступен на http://localhost"
else
    log "WARN — health check не прошёл, смотри логи:"
    $COMPOSE logs backend --tail=20
fi

log "=== Deploy завершён ==="
