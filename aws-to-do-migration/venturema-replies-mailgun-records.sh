#!/usr/bin/env bash
# Add Mailgun/LeadConnector records for the replies.venturema.co.uk subdomain to DO DNS.
# Token via env (don't hardcode secrets):  DO_TOKEN=dop_v1_... bash venturema-replies-mailgun-records.sh
# Gotchas handled: relative hostnames; trailing dots on CNAME/MX targets so DO doesn't append the zone.
set -euo pipefail
: "${DO_TOKEN:?set DO_TOKEN}"
DOM=venturema.co.uk
d(){ doctl compute domain records create "$DOM" -t "$DO_TOKEN" "$@"; }

d --record-type TXT   --record-name replies              --record-data "v=spf1 include:spf.leadconnectorhq.com include:mailgun.org ~all"
d --record-type TXT   --record-name smtp._domainkey.replies --record-data "k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCzOoL5TBAsppKmmiWh+mjwgHvCH2Jei2+2Qsr/ho36xo9Sb7PRYW3MM8dyzBvGDEXaKQgHTTLbyBBPhDp4SO7/en30kJMxMqVHHWvx7T9z2UlLpl0QUVWwtF2plzQIglKWkAnqBQK7TUU9hAzBnyvi8qxQry6f8y34pgyv0lj5fQIDAQAB"
d --record-type CNAME --record-name email.replies        --record-data "mailgun.org."
d --record-type MX    --record-name replies              --record-priority 10 --record-data "mxa.mailgun.org."
d --record-type MX    --record-name replies              --record-priority 10 --record-data "mxb.mailgun.org."
d --record-type TXT   --record-name _dmarc.replies       --record-data "v=DMARC1;p=none;"

echo "Done. Verify:  doctl compute domain records list $DOM -t \$DO_TOKEN | grep replies"
