#! /usr/bin/env sh

dir="/etc/apache2/sites-available/"

if [ $# -eq 0 ] || [ $# -gt 2 ]
then
  echo "Usage:" $(basename $0) "hostname [config=def]" >&2
  exit 1
fi

host="$1"
if [ $# -eq 2 ]
then
  conf="$2"
else
  conf="def"
fi

def="/etc/sitegen/${conf}"
def_conf="/etc/sitegen/${conf}.conf"

adef="${dir}/${host}"
adef_conf="${dir}/${host}.conf"

if [ ! -f "${def}" ] || [ ! -f "${def_conf}" ]
then
  echo "Configuration file ${def} and/or ${def_conf} error: No such file" >&2
  exit 2
fi

if [ -f "${adef}" ] || [ -f "${adef_conf}" ]
then
  echo "Host already exists: ${adef} and/or ${adef_conf}" >&2
  exit 3
fi

sed="s/%%HOST%%/${host}/g"
sed "${sed}" "${def}" > "${adef}"
sed "${sed}" "${def_conf}" > "${adef_conf}"
mkdir -p "/var/${host}"
