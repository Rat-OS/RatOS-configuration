#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
tail -n +2 "$SCRIPT_DIR"/../templates/v-core-pro-printer.template.cfg > "$SCRIPT_DIR"/../../printer.cfg
