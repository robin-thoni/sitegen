#! /usr/bin/env sh

if [ $# -ne 2 ]
then
    name=$(basename "$0")
    echo "Usage: ${name} directory checkend" >&2
    exit 64
fi

dir="$1"
checkend="$2"

certs=$(cert-check "${dir}" "${checkend}")

echo "${certs}"

sites=$(echo "${certs}" | cut -d' ' -f1)

for site in ${sites}
do
  echo
  generate-ssl-cert "${site}"
done
