#!/bin/sh
cd "$(dirname "$0")" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
python3 server.py
status=$?
if [ "$status" -ne 0 ]; then
  printf '\n启动失败，请查看上方提示。按回车关闭。'
  read answer
fi
exit "$status"
