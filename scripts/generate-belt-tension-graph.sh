#!/bin/bash
set -e -u -o pipefail
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

## the TEST_RESONANCES command seems to return before all data is completely
## written. it'd be better to poll for the files to be completely written,
## but this has been reliable for me so far…
sleep 10

outdir="${SCRIPT_DIR}"../../input_shaper
if [ ! -d "${outdir}" ]; then
    mkdir "${outdir}"
fi

~/klipper/scripts/graph_accelerometer.py \
    -c /tmp/raw_data_axis*_belt-tension-*.csv \
    -o "${outdir}/belt-tension-resonances-$( date +'%Y-%m-%d-%H%M%S' ).png"
