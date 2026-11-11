#!/bin/sh
# Deliberately configured container-local cases; never changes the host.
set -eu
for profile in conforming mixed nonconforming incomplete; do
  root=/lab/live/$profile
  mkdir -p "$root/data" "$root/install" "$root/logs"
  printf 'retention_days=%s\n' 30 > "$root/retention.conf"
  printf 'customer-record-for-deletion-test\n' > "$root/data/expired-record.txt"
  printf 'business-records-backup\n' > "$root/backup.dat"
  sha256sum "$root/backup.dat" | cut -d ' ' -f 1 > "$root/backup.sha256"
  cp "$root/backup.dat" "$root/restored.dat"
  printf 'read-only-business-record\n' > "$root/data/restricted.txt"
  chmod 644 "$root/data/restricted.txt"
  printf 'subject,decision,reviewed_at\nlabworker,approved,%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$root/access-review.csv"
  chmod 755 "$root/install" "$root/logs"
  printf 'event=application_start actor=lab-service\n' >> "$root/logs/application.log"
  sha256sum "$root/logs/application.log" | cut -d ' ' -f 1 > "$root/logs/application.sha256"
  dpkg-query -W -f='${Package}\t${Version}\n' | sort > "$root/installed.tsv"
  cp "$root/installed.tsv" "$root/approved.tsv"
  if [ "$profile" = conforming ]; then rm "$root/data/expired-record.txt"; fi
  if [ "$profile" = mixed ] || [ "$profile" = nonconforming ]; then
    printf 'subject,decision,reviewed_at\nlabworker,rejected,%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$root/access-review.csv"
    printf 'restore-does-not-match\n' > "$root/restored.dat"
    printf 'event=changed-after-integrity-seal\n' >> "$root/logs/application.log"
    printf 'not-the-installed-inventory\n' > "$root/approved.tsv"
  fi
  if [ "$profile" = nonconforming ]; then
    printf 'retention_days=365\n' > "$root/retention.conf"
    printf 'backup-corrupted-after-seal\n' >> "$root/backup.dat"
    chmod 666 "$root/data/restricted.txt"
    chmod 777 "$root/install"
    # No application event was actually recorded in this case.
    : > "$root/logs/application.log"
  fi
  if [ "$profile" = incomplete ]; then
    rm "$root/restored.dat" "$root/access-review.csv" "$root/approved.tsv" "$root/logs/application.sha256"
    # Absence of verification receipt must remain unknown even if the object exists.
  else
    printf 'deletion-check-authorized\n' > "$root/deletion-receipt"
  fi
done
