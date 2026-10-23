#!/bin/bash
# php2shell (CVE-2026-109618/109619) stopgap for the oakhill AWS EC2 (Ubuntu 20.04, php7.4-fpm).
# Run: ssh ubuntu@54.155.196.25 'bash -s' < oakhill-php2shell-mitigate.sh
# Rollback: sudo rm /etc/php/7.4/fpm/conf.d/99-security-hardening.ini /etc/systemd/system/php7.4-fpm.service.d/memory-cap.conf
#           sudo cp /root/php2shell-<ts>/fpm/pool.d/www.conf /etc/php/7.4/fpm/pool.d/www.conf
#           sudo systemctl daemon-reload && sudo systemctl restart php7.4-fpm
set -euo pipefail
ts=$(date +%Y%m%d%H%M%S)
sudo mkdir -p /root/php2shell-$ts
sudo cp -a /etc/php/7.4/fpm /root/php2shell-$ts/
echo "backup: /root/php2shell-$ts"

if grep -q "php2shell" /etc/php/7.4/fpm/pool.d/www.conf; then
  echo "pool already has the php2shell block, not appending again"
else
  sudo tee -a /etc/php/7.4/fpm/pool.d/www.conf >/dev/null <<EOF

; php.net advisory mitigation for CVE-2026-109618 (php2shell), added $(date +%F) by Developyn.
; php_admin_value so WordPress cannot lower it; systemd MemoryMax caps php-fpm instead.
php_admin_value[memory_limit] = -1
request_terminate_timeout = 120s
EOF
fi

# disable_functions in conf.d replaces the php.ini value, so carry the original list over.
old=$(grep -E "^disable_functions" /etc/php/7.4/fpm/php.ini | sed "s/^disable_functions = //; s/,$//")
sudo tee /etc/php/7.4/fpm/conf.d/99-security-hardening.ini >/dev/null <<EOF
; Stopgap for CVE-2026-109618 / CVE-2026-109619 ("php2shell"), added $(date +%F) by Developyn.
; Ubuntu 20.04 php7.4 is only patched via Ubuntu Pro (7.4.3-4ubuntu2.29+esm5).
; Remove once the patched package is installed or the site moves to DigitalOcean.
disable_functions = $old,exec,passthru,shell_exec,system,proc_open,popen
session.upload_progress.enabled = 0
EOF

sudo mkdir -p /etc/systemd/system/php7.4-fpm.service.d
sudo tee /etc/systemd/system/php7.4-fpm.service.d/memory-cap.conf >/dev/null <<EOF
# Backstop for php_admin_value[memory_limit] = -1 (php2shell mitigation), added $(date +%F).
[Service]
MemoryMax=280M
MemoryLimit=280M
EOF

sudo php-fpm7.4 -t
sudo systemctl daemon-reload
sudo systemctl restart php7.4-fpm
sleep 2

echo "--- checks"
echo "php7.4-fpm: $(systemctl is-active php7.4-fpm)"
echo "cgroup limit: $(cat /sys/fs/cgroup/memory/system.slice/php7.4-fpm.service/memory.limit_in_bytes 2>/dev/null || cat /sys/fs/cgroup/system.slice/php7.4-fpm.service/memory.max)"
sudo php-fpm7.4 -tt 2>&1 | grep -E "memory_limit|request_terminate_timeout" | sed 's/^.*NOTICE: *//'
sudo php-fpm7.4 -i | grep -E "^(disable_functions|session.upload_progress.enabled)" | cut -c1-200
for u in https://oakhilloptical.co.uk/ https://oakhilloptical.co.uk/wp-login.php https://oakhilloptical.co.uk/wp-json/; do
  curl -s -o /dev/null --resolve oakhilloptical.co.uk:443:127.0.0.1 -w "%{http_code} $u\n" "$u"
done
sudo tail -n 5 /var/log/php7.4-fpm.log
