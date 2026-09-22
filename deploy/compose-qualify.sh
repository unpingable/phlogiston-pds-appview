#!/bin/sh
# Local-only operator helper. It refuses a floating image before Compose sees it.
set -eu
: "${PHLOGISTON_RENDER_IMAGE:?set image@sha256:...}"
: "${PHLOGISTON_RUN_ID:?set a new run id}"
: "${PHLOGISTON_SOURCE_REVISION:?set exact source revision}"
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
python3 "$project_dir/deploy/validate_image.py" "$PHLOGISTON_RENDER_IMAGE"
mkdir -p "$project_dir/deploy/output-parent"
exec docker compose -f "$project_dir/deploy/compose.synthetic.yaml" run --rm render
