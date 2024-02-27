#!/bin/sh

ARTI_WEBHOOK_USER="example"
ARTI_WEBHOOK_PASS="example_password"
ARTI_WEBHOOK_HOST="lowside.example.com/pipelines/api"
ARTI_WEBHOOK_NUM="5" # From the JFrog Pipelines Webhook Integration

curl --insecure -T pypi.json -H'Content-Type:application/json' -XPOST "https://${ARTI_WEBHOOK_USER}:${ARTI_WEBHOOK_PASS}@${ARTI_WEBHOOK_HOST}/v1/projectIntegrations/${ARTI_WEBHOOK_NUM}/hook"
