#!/bin/bash
# Setup script for QAB on a new machine.
#
# This makes the QAB project runnable by adding the vendor/ directory
# to the Python path so that `micro_qml` imports resolve.
#
# Usage:
#   source setup.sh
#   # or add to .bashrc/.zshrc:
#   # export PYTHONPATH="$PWD/vendor:$PYTHONPATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PYTHONPATH="${SCRIPT_DIR}/vendor:${SCRIPT_DIR}/../..:${PYTHONPATH}"

echo "QAB environment configured:"
echo "  PYTHONPATH includes: ${SCRIPT_DIR}/vendor"
echo "  PYTHONPATH includes: ${SCRIPT_DIR}/../.."
echo ""
echo "Verify with:"
echo "  python -m projects.QAB.atlas.query --summary"
