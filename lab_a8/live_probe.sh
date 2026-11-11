#!/bin/sh
# Read-only observations at collection time. Names are fixed, never caller paths.
set -eu
case "$1" in conforming|mixed|nonconforming|incomplete) ;; *) exit 64;; esac
case "$2" in
  A.8.3|A.8.10|A.8.13|A.8.15|A.8.19) ;;
  A.8.1|A.8.2|A.8.5|A.8.7|A.8.8|A.8.9|A.8.12|A.8.16|A.8.17|A.8.20|A.8.22|A.8.24|A.8.32)
    exec python /extended_probe.py probe "$1" "$2" ;;
  *) exit 64;;
esac
root=/lab/live/$1
emit() {
  printf '%s\t' "$1"
  if [ -r "$2" ]; then base64 -w 0 "$2"; else printf 'MISSING'; fi
  printf '\n'
}
value() { printf '%s\t' "$1"; printf '%s' "$2" | base64 -w 0; printf '\n'; }
value observed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
value asset_id "$(hostname)"
case "$2" in
  A.8.3)
    if su -s /bin/sh labworker -c "test -w '$root/data/restricted.txt'"; then rc=0; else rc=$?; fi
    value write_access_rc "$rc"
    value resource_stat "$(stat -c '%a %U %G' "$root/data/restricted.txt")"
    emit access-review.csv "$root/access-review.csv"
    ;;
  A.8.10)
    emit retention.conf "$root/retention.conf"
    emit deletion-receipt "$root/deletion-receipt"
    if [ -e "$root/data/expired-record.txt" ]; then rc=0; else rc=1; fi
    value object_exists_rc "$rc"
    ;;
  A.8.13)
    emit backup.dat "$root/backup.dat"
    emit backup.sha256 "$root/backup.sha256"
    emit restored.dat "$root/restored.dat"
    ;;
  A.8.15)
    emit application.log "$root/logs/application.log"
    emit application.sha256 "$root/logs/application.sha256"
    value resource_stat "$(stat -c '%a %U %G' "$root/logs/application.log")"
    ;;
  A.8.19)
    if su -s /bin/sh labworker -c "test -w '$root/install'"; then rc=0; else rc=$?; fi
    value install_access_rc "$rc"
    value install_stat "$(stat -c '%a %U %G' "$root/install")"
    # Query the package database now; do not reuse a prepared status Boolean.
    printf 'installed.tsv\t'
    dpkg-query -W -f='${Package}\t${Version}\n' | sort | base64 -w 0
    printf '\n'
    emit approved.tsv "$root/approved.tsv"
    ;;
esac
