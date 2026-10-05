#!/usr/bin/env bash
# 用 Mac 的 `shortcuts sign` 簽 tools/unsigned/ 的捷徑，結果放到 shortcuts/（這份才進 repo、給 iPhone 匯入）
# 用法：tools/sign-on-mac.sh <mac-ssh-host>
set -euo pipefail
mac=${1:?usage: sign-on-mac.sh <mac-ssh-host>}
cd "$(dirname "$0")/.."
python3 tools/build-shortcuts.py >/dev/null
tmp=$(ssh "$mac" mktemp -d)
scp -q tools/unsigned/*.shortcut "$mac:$tmp/"
ssh "$mac" "cd $tmp && for f in *.shortcut; do shortcuts sign --mode anyone -i \"\$f\" -o \"signed-\$f\"; done"
mkdir -p shortcuts
for f in tools/unsigned/*.shortcut; do n=$(basename "$f"); scp -q "$mac:$tmp/signed-$n" "shortcuts/$n"; done
ssh "$mac" rm -rf "$tmp"
ls -la shortcuts/
