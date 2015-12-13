#! /usr/bin/env bash

if [ $# -eq 0 ]
then
  echo "Usage: generate-ssl-cert hostname [options]" >&2
  exit 64
fi

host="$1"

letsencrypt --agree-tos --renew-by-default --standalone --standalone-supported-challenges http-01 --http-01-port 9999 --server https://acme-v01.api.letsencrypt.org/directory certonly -d $*

if [ $? -ne 0 ]
then
  echo "Failed to generate certificate" >&2
  exit 1
fi

ln -sf /etc/letsencrypt/live/${host}/cert.pem /etc/ssl/private/${host}.crt
ln -sf /etc/letsencrypt/live/${host}/privkey.pem /etc/ssl/private/${host}.key
ln -sf /etc/letsencrypt/live/${host}/chain.pem /etc/ssl/private/${host}-chain.crt
