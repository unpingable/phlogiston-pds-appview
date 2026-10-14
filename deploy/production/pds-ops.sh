#!/bin/sh
set -eu
# Package source lives beside the deployment kit; no environment or secrets echoed.
kit=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
export PYTHONPATH="$kit/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m phlogiston_appview.pds_ops "$@"
