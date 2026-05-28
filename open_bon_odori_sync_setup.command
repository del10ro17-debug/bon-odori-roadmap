#!/bin/bash
cd "$(dirname "$0")"
chmod +x tools/bon_odori_attendance/setup-github-sync.sh
./tools/bon_odori_attendance/setup-github-sync.sh
read -r -p "Enter で終了"
