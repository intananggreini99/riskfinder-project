# mlflow-server/Caddy.Dockerfile
# ===========================================================================
# Membungkus Caddyfile ke dalam image Caddy resmi agar bisa di-deploy sebagai
# service "Caddy" di Railway (Topologi 2 dengan Basic Auth — Bab 6).
#
# Di Railway, buat service Caddy dari repo ini lalu set:
#   Settings -> Root Directory   = mlflow-server
#   Settings -> Dockerfile Path  = Caddy.Dockerfile
# (Service MLflow tetap memakai ./Dockerfile yang default.)
#
# Caddy resmi otomatis menjalankan:
#   caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
# sehingga $PORT, $AUTH_USER, dan $AUTH_PASSWORD_HASH terbaca dari environment.
# ===========================================================================
FROM caddy:2-alpine

COPY Caddyfile /etc/caddy/Caddyfile
