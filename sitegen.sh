#! /usr/bin/env sh

apache_dir=/etc/apache2/sites-available/
conf_dir=/etc/sitegen/
site_dir=/var/

hooks_dir=/etc/sitegen/hooks.d/
hooks_dir_local=~/.sitegen/hooks.d/

makeDir()
{
  mkdir -p "$1"
  if [ $? -ne 0 ]
  then
    exit 4
  fi
}

getPath()
{
  readlink -m "$1"
}

applyHooks()
{
  dir="$1"
  if [ -d ${dir} ]
  then
    for file in $(find ${dir} | sort) ;
    do
      echo "Applying ${file}"
      . "${file}"
    done
  else
    echo "No hooks found in ${dir}"
  fi
}


if [ $# -eq 0 ] || [ $# -gt 2 ] || [ "$1" = "--help" ]
then
  echo "Usage:" $(basename $0) "hostname [config=default]" >&2
  exit 1
fi

host="$1"
if [ $# -eq 2 ]
then
  conf="$2"
else
  conf="default"
fi

conf_conf=$(getPath "${conf_dir}/${conf}.conf")
conf_include=$(getPath "${conf_dir}/${conf}.include")

site_conf=$(getPath "${apache_dir}/${host}.conf")
site_include=$(getPath "${apache_dir}/${host}.include")

root_dir=$(getPath "${site_dir}/${host}")

sed_host="s:%%HOST%%:${host}:g"
sed_root="s:%%ROOT%%:${root_dir}:g"

if [ ! -f "${conf_conf}" ] || [ ! -f "${conf_include}" ]
then
  echo "Configuration file ${conf_conf} and/or ${conf_include} error: No such file" >&2
  exit 2
fi

if [ -f "${site_conf}" ] || [ -f "${site_include}" ]
then
  echo "Host already exists: ${site_conf} and/or ${site_include}" >&2
  exit 3
fi

makeDir "${root_dir}"
makeDir "${apache_dir}"

sed -e "${sed_host}" -e "${sed_root}" "${conf_conf}" > "${site_conf}"
sed -e "${sed_host}" -e "${sed_root}" "${conf_include}" > "${site_include}"

applyHooks ${hooks_dir}
applyHooks ${hooks_dir_local}
