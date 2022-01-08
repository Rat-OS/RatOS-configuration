#!/bin/bash
set -e -u -o pipefail

## the TEST_RESONANCES command seems to return before all data is completely
## written. it'd be better to poll for the files to be completely written,
## but this has been reliable for me so far…
sleep 10

~/klipper/scripts/graph_accelerometer.py \
    -c /tmp/raw_data_axis*_belt-tension-*.csv \
    -o /tmp/belt-tension-resonances.png
