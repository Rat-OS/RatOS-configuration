#!/bin/bash
verified=1

while IFS= read -r -d '' file; do
    if [ ! -x "$file" ]; then
        echo "$file is not executable"
        verified=0
    fi
done < <(find . -iname "*.sh" -print0)

if [ $verified -eq 0 ]; then
    echo "Some scripts are not executable. Please fix this."
    exit 1
fi
echo "All scripts are executuable! :)"