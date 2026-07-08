#!/usr/bin/env bash
# Replicate venturema.co.uk zone into DigitalOcean DNS (free), end-state = cut over to DO host.
# Mirrors Route 53 zone Z07070082E15ZM5DTXD3X exactly, minus NS/SOA (DO manages those).
# Run AFTER reviewing. Owner must then repoint registrar NS to ns1/ns2/ns3.digitalocean.com.
set -euo pipefail

DOM=venturema.co.uk
NEW_IP=142.93.41.146   # DO host. Use 3.249.250.224 instead for a pure DNS-host move (no server cutover yet).

# Creates the domain + apex A in one call, plus DO's own NS records.
doctl compute domain create "$DOM" --ip-address "$NEW_IP"

# Mail: Google Workspace MX (priority host)
doctl compute domain records create "$DOM" --record-type MX --record-name @ --record-priority 1  --record-data aspmx.l.google.com.
doctl compute domain records create "$DOM" --record-type MX --record-name @ --record-priority 5  --record-data alt1.aspmx.l.google.com.
doctl compute domain records create "$DOM" --record-type MX --record-name @ --record-priority 5  --record-data alt2.aspmx.l.google.com.
doctl compute domain records create "$DOM" --record-type MX --record-name @ --record-priority 10 --record-data alt3.aspmx.l.google.com.
doctl compute domain records create "$DOM" --record-type MX --record-name @ --record-priority 10 --record-data alt4.aspmx.l.google.com.

# Verification TXT (apex)
doctl compute domain records create "$DOM" --record-type TXT --record-name @ --record-ttl 300 \
  --record-data "google-site-verification=TxxhcrKLaT7evcC6VeyhQnsih_wQxGJ1KDXcCzAAgKc"

# DKIM TXT (zmail selector)
doctl compute domain records create "$DOM" --record-type TXT --record-name zmail._domainkey --record-ttl 300 \
  --record-data "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC9T0oqsRg/5ZT8oMZLnCNZN+2b/ETp24EvxJG/bs0nM/03ULD/lyuniUUC1sgTwb71GoHrjf2a8/cY/Y3XlRT+JC6Zi8Gh4DjE/JW351LelwZoW+TLTMQXsC1awHvSMdG8Y61RvXy+uczsTYXIA5AT6JZiv7EiSWoJK01VhGXaBwIDAQAB"

# www -> apex
doctl compute domain records create "$DOM" --record-type CNAME --record-name www --record-data @ --record-ttl 300

echo "Done. Verify:  doctl compute domain records list $DOM"
