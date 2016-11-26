#! /usr/bin/env sh

dir="$(dirname $(readlink -f "${0}"))"
arg="${1}"
d="${2}"
host="${3}"

if [ "${host}" = "error.com" ] || [ "${arg}" != "Test." ] || [ "${d}" != "-d" ]
then
    echo "Failed to get certificate" >&2
    exit 1
fi &&

if [ "${host}" = "" ]
then
    echo "No domain" >&2
    exit 1
fi &&

leDir="${dir}/etc/letsencrypt/live/${host}"

echo $leDir

mkdir -p "${leDir}" &&
scp serv3:/etc/letsencrypt/live/${host}/* "${leDir}"