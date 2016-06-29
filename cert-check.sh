#! /usr/bin/env sh

if [ $# -ne 2 ]
then
  echo "Usage: cert-check directory checkend" >&2
  exit 64
fi

dir="$1"
checkend="$2"

for cert in ${dir}/*.crt
do
  openssl x509 -noout -in "${cert}" -checkend "${checkend}"
  will_expire="$?"
  date="$(openssl x509 -noout -in "${cert}" -enddate | cut -d= -f2)"
  if [ "${will_expire}" -eq 1 ]
  then
    site=$(basename "${cert}")
    site=$(echo "${site}" | sed -re 's/(.+).crt/\1/')
    echo "${site}" "${date}"
  fi
done
