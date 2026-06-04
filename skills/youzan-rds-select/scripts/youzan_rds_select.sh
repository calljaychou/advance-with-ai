#!/usr/bin/env bash
set -euo pipefail

url="https://diy.youzanyun.com/api/rds/exec-dml?"
limit="500"

sid=""
zone=""
db_name=""
biz_ins_id=""
app_id=""
statement=""

usage() {
  cat <<'EOF'
Usage:
  youzan_rds_select.sh --sid <sid> --zone <zone> --db-name <dbName> --biz-ins-id <bizInsId> --app-id <appId> --statement <select_sql>

Options:
  --sid          有赞 Cookie 中的 sid 值
  --zone         环境，例如 prod
  --db-name      RDS 数据库名称
  --biz-ins-id   有赞业务实例 ID
  --app-id       有赞应用 ID
  --statement    只读 SELECT SQL
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sid)
      sid="${2:-}"
      shift 2
      ;;
    --zone)
      zone="${2:-}"
      shift 2
      ;;
    --db-name)
      db_name="${2:-}"
      shift 2
      ;;
    --biz-ins-id)
      biz_ins_id="${2:-}"
      shift 2
      ;;
    --app-id)
      app_id="${2:-}"
      shift 2
      ;;
    --statement)
      statement="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$sid" || -z "$zone" || -z "$db_name" || -z "$biz_ins_id" || -z "$app_id" || -z "$statement" ]]; then
  echo "Missing required arguments." >&2
  usage >&2
  exit 2
fi

trimmed_statement="$(printf '%s' "$statement" | sed -E 's/^[[:space:]]+//')"
statement_head="$(printf '%s' "$trimmed_statement" | tr '[:lower:]' '[:upper:]' | cut -c 1-6)"

if [[ "$statement_head" != "SELECT" ]]; then
  echo "Only SELECT statements are allowed." >&2
  exit 2
fi

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read())[1:-1])'
}

escaped_statement="$(printf '%s' "$statement" | json_escape)"
escaped_zone="$(printf '%s' "$zone" | json_escape)"
escaped_db_name="$(printf '%s' "$db_name" | json_escape)"
escaped_biz_ins_id="$(printf '%s' "$biz_ins_id" | json_escape)"
escaped_app_id="$(printf '%s' "$app_id" | json_escape)"

payload="{\"statement\":\"$escaped_statement\",\"limit\":$limit,\"dbName\":\"$escaped_db_name\",\"bizInsId\":\"$escaped_biz_ins_id\",\"appId\":\"$escaped_app_id\",\"zone\":\"$escaped_zone\"}"

curl --silent --show-error \
  --request POST "$url" \
  --header "Content-Type: application/json" \
  --header "Cookie: sid=$sid" \
  --data "$payload"
