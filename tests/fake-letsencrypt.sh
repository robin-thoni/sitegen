#! /usr/bin/env sh

dir="$(dirname $(readlink -f "${0}"))"
host="${1}"

if [ "${host}" = "error.com" ]
then
    echo "Failed to get certificate" >&2
    exit 1
fi &&

if [ "${host}" = "" ]
then
    echo "No domain" >&2
    exit 1
fi &&

leDir="${dir}/tests/etc/letsencrypt/live/${host}"


mkdir -p "${leDir}" &&
scp serv3:/etc/letsencrypt/live/${host}/* tests/etc/letsencrypt/live/${host}/