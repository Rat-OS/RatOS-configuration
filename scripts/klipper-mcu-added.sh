#!/bin/sh
logfile="/var/log/ratos.log"
printer="/tmp/printer"

touch "$logfile"
chmod 664 "$logfile"

echo "$(date +"%Y-%m-%d %T"): MCU Detected" >> "$logfile"

# If [ -h $printer] is true but [ -e $printer is false ] $printer is probably
# a symbolic link in a directory with the sticky bit set, or one of the links
# in a chain of symlinks is in a directory with the sticky bit set.
# In this case, it will not be possible to write to $printer if that symlink
# it is owned by a different user. /tmp often has the sticky bit set. 
#
# Dereference and keep dereferencing until $printer points to a file or 
# symlink to which the RESTART command can actually be written

while [ ! -e $printer ] && [ -h $printer ]
do
    printer=$(readlink $printer)
done

if [ -e $printer ]; then
    echo "RESTART" > $printer
    echo "$(date +"%Y-%m-%d %T"): RESTART command sent to $printer" >> "$logfile"
else
    echo "$(date +"%Y-%m-%d %T"): $printer does not exist" >> "$logfile"
fi
