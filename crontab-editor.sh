#!/bin/bash

# This script is a simple crontab editor that allows you to add, remove, and list cron jobs.

# Usage:
#
#   EDITOR=./crontab-editor.sh crontab -e

set -ex

cd -- "$PPWD" # a trick

# First get the minutes
minutes1=$(( RANDOM % 60 ))
if [ $minutes1 -ge 30 ]; then
    minutes1=$(( minutes1 - 30 ))
fi
minutes2=$(( minutes1 + 30 ))
MINUTES="$minutes1,$minutes2"
export MINUTES
echo $MINUTES


crontab_file="$1"
new_command="`cat crontab.in | envsubst | grep magic=`" # This is the new command to add to the crontab file
magic_string=${new_command##*magic=} # This is the magic string that we're going to look for in the crontab file
tmp_file="`mktemp`"
trap 'rm -f -- "$tmp_file"' EXIT
grep -v -- "$magic_string" < "$crontab_file" > "$tmp_file"
echo "$new_command" >> "$tmp_file"
cat "$tmp_file" > "$crontab_file" # Take care not to unlink the crontab file, it must be overwritten in place.