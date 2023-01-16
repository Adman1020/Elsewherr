#! /bin/sh

if [ "${SCHEDULE}" = "None" ]; then
  python /usr/src/app/elsewherr.py
else
  echo "${SCHEDULE} python /usr/src/app/elsewherr.py" | crontab - && crond -f -L /dev/stdout
fi
