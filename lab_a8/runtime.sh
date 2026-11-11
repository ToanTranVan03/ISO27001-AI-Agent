#!/bin/sh
set -eu
mkdir -p /lab/export
cp -R /fixtures/. /lab/export/
# Only container-local accounts/files are touched. No host paths or published ports.
id labworker >/dev/null 2>&1 || useradd -m labworker
for profile in conforming mixed nonconforming incomplete; do
  root=/lab/export/$profile
  file="$root/A.8.13/backup.dat"
  if [ "$profile" = nonconforming ]; then printf 'tampered-after-manifest\n' >> "$file"; fi
  if [ "$profile" = conforming ]; then cp "$file" "$root/A.8.13/restored.dat"; fi
  deletion="$root/A.8.10/expired-record.txt"
  printf 'synthetic customer record\n' > "$deletion"
  if [ "$profile" = conforming ]; then rm "$deletion"; fi
  if [ "$profile" != incomplete ]; then
    if [ -e "$deletion" ]; then outcome=still_present; else outcome=absent; fi
    printf 'ticket=DEL-01 action=remove verification=%s\n' "$outcome" > "$root/A.8.10/deletion.log"
  fi
  install="$root/A.8.19/packages-dir"
  mkdir -p "$install"
  if [ "$profile" = nonconforming ]; then chmod 777 "$install"; else chmod 755 "$install"; fi
  if su -s /bin/sh labworker -c "test -w '$install'"; then permission=allow; else permission=deny; fi
  printf 'subject,install_permission\nadmin,allow\nuser,%s\n' "$permission" > "$root/A.8.19/installer-permissions.csv"
  # A raw audit record of executed container-local probes, distinct from authored fixtures.
  printf 'account=labworker uid=%s install_write=%s backup_sha256=%s\n' "$(id -u labworker)" "$permission" "$(sha256sum "$file" | cut -d ' ' -f 1)" > "$root/runtime-probes.log"
done
/bin/sh /live_setup.sh
printf 'ready\n' > /lab/ready
exec tail -f /dev/null
