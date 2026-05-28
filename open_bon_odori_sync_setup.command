#!/bin/bash
cd "$(dirname "$0")"
chmod +x tools/bon_odori_attendance/copy-gas-code.sh 2>/dev/null || true
./tools/bon_odori_attendance/copy-gas-code.sh
open "docs/bon-odori/共有の始め方.md"
open "https://script.google.com/home/projects/1HEtZQX8m2K_VOtblWEaY5x6qKVghx-EVCJ8SBw6tgySagYuzKSpduBlC/edit"
