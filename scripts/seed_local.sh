#!/usr/bin/env bash
# Seed the local NutriWise API with a handful of approved nutritionists.
#
# Prereq: API running at localhost:8000 with ENV=dev (dev bypass on so the
# X-User-Id/X-User-Role headers are trusted). Run from anywhere — the script
# only talks to the HTTP API.
set -euo pipefail

BASE="${NUTRIWISE_API:-http://localhost:8000}"
ADMIN=(-H "X-User-Id: admin" -H "X-User-Role: admin")

register() {
  curl -sS -X POST "$BASE/v1/nutritionists" \
    -H "Content-Type: application/json" "${ADMIN[@]}" \
    -d "$1" | python3 -c 'import sys,json; print(json.load(sys.stdin)["nutritionist_id"])'
}

approve() {
  curl -sS -X POST "$BASE/v1/nutritionists/$1/verify?status=approved" "${ADMIN[@]}" >/dev/null
}

seed_one() {
  local id
  id=$(register "$1")
  approve "$id"
  echo "  ✓ $id"
}

echo "Seeding nutritionists against $BASE …"

seed_one '{"name":"Priya Menon","email":"priya.menon@example.com","country":"IN","city":"Mumbai","credentials":["IDA-RD"],"specialties":["diabetes","pcos"],"languages":["en","hi"],"virtual_rate":2500,"in_home_rate":3500,"bio":"Evidence-based guidance with a practical, sustainable approach."}'
seed_one '{"name":"Neha Shah","email":"neha.shah@example.com","country":"IN","city":"Delhi","credentials":["IDA-RD"],"specialties":["prenatal","pediatric"],"languages":["en","hi"],"virtual_rate":2200,"bio":"Prenatal and pediatric nutrition specialist."}'
seed_one '{"name":"Vikram Rao","email":"vikram.rao@example.com","country":"IN","city":"Chennai","credentials":["MSc-Nutrition"],"specialties":["gut_health","weight_loss"],"languages":["en","hi","ta"],"virtual_rate":1900,"in_home_rate":2800,"bio":"Gut health and sustainable weight management."}'
seed_one '{"name":"Arjun Kapoor","email":"arjun.kapoor@example.com","country":"IN","city":"Bengaluru","credentials":["MSc-Nutrition"],"specialties":["sports","weight_loss"],"languages":["en","hi","kn"],"virtual_rate":1800,"bio":"Sports nutrition for athletes and fitness enthusiasts."}'

seed_one '{"name":"Emily Chen","email":"emily.chen@example.com","country":"US","city":"San Francisco","credentials":["RDN"],"specialties":["gut_health","plant_based"],"languages":["en","zh"],"virtual_rate":120,"in_home_rate":180,"bio":"RDN focused on plant-forward, gut-friendly nutrition."}'
seed_one '{"name":"Sophie Ramirez","email":"sophie.ramirez@example.com","country":"US","city":"Los Angeles","credentials":["CNS"],"specialties":["sports","weight_loss"],"languages":["en","es"],"virtual_rate":140,"in_home_rate":200,"bio":"Sports nutrition + sustainable fat loss."}'
seed_one '{"name":"Jordan Park","email":"jordan.park@example.com","country":"US","city":"New York","credentials":["RDN"],"specialties":["pcos","plant_based"],"languages":["en","ko"],"virtual_rate":160,"bio":"Hormonal health, PCOS, plant-based nutrition."}'
seed_one '{"name":"Marcus Hale","email":"marcus.hale@example.com","country":"US","city":"Austin","credentials":["RD"],"specialties":["weight_loss","diabetes"],"languages":["en","es"],"virtual_rate":95,"bio":"Diabetes management and weight loss."}'

echo "Done."
echo "  US: $(curl -sS "$BASE/v1/nutritionists?country=US" "${ADMIN[@]}" | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))')"
echo "  IN: $(curl -sS "$BASE/v1/nutritionists?country=IN" "${ADMIN[@]}" | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))')"
