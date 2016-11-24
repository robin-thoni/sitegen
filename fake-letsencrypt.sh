#! /usr/bin/env sh

dir="$(dirname $(readlink -f "${0}"))"
host="${1}"

if [ "${host}" = "error.com" ]
then
    echo "Failed to get certificate" >&2
    exit 1
fi

leDir="${dir}/tests/etc/letsencypt/live/${host}"

sleep 1

mkdir -p "${leDir}"
touch "${leDir}/cert.pem" "${leDir}/privkey.pem" "${leDir}/chain.pem"
echo "Generation successful"