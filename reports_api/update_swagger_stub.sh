#!/bin/bash
# Swagger generate server stub based on specification, then merge it into the project.
# Use carefully! Commit always before using this script!

# Variables
STUB_DIR=python-flask-server-generated
WORKING_DIR=openapi_server
ARCHIVE_DIR=openapi_server_archive
SCRIPTS_DIR=$(pwd)

FILES_TO_COPY=(
  __init__.py
  __main__.py
)

DIRS_TO_COPY=(
  response
)

# Generate server stub
openapi-generator generate -i openapi.yml -l python-flask -o "${STUB_DIR}"

# Ensure stub was created
if [ ! -d "$STUB_DIR/openapi_server" ]; then
    echo "[ERROR] Unable to find ${STUB_DIR}/openapi_server"
    exit 1
fi

# Replace imports in all generated .py files
find "${STUB_DIR}/openapi_server" -type f -name "*.py" -print0 | \
xargs -0 sed -i '' \
    -e 's/from openapi_server\./from reports_api.openapi_server./g' \
    -e 's/from openapi_server /from reports_api.openapi_server /g' \
    -e 's/import openapi_server\./import reports_api.openapi_server./g' \
    -e 's/import openapi_server/import reports_api.openapi_server/g'

# Archive the old working directory
if [ -d "$ARCHIVE_DIR" ]; then
    rm -rf "$ARCHIVE_DIR"
fi
echo "[INFO] full copy of '${WORKING_DIR}' archived as '${ARCHIVE_DIR}'"
cp -r "$WORKING_DIR" "$ARCHIVE_DIR"

# Replace working directory with newly generated stub
rm -rf "$WORKING_DIR"
echo "[INFO] create new '${WORKING_DIR}' from '${STUB_DIR}'"
cp -r "${STUB_DIR}/openapi_server" "$WORKING_DIR"

# Copy preserved directories and files
for f in "${DIRS_TO_COPY[@]}"; do
    echo "[INFO] copy directory: ${f} to new ${WORKING_DIR}"
    cp -r "$ARCHIVE_DIR/${f}" "$WORKING_DIR/${f}"
done

for f in "${FILES_TO_COPY[@]}"; do
    echo "[INFO] copy file: ${f} to new ${WORKING_DIR}"
    cp "$ARCHIVE_DIR/${f}" "$WORKING_DIR/${f}"
done

# Update controller files
echo "[INFO] update controllers to include response import"
for f in "$WORKING_DIR/controllers/"*.py; do
    fname=$(basename "$f")
    if [[ "$fname" == __* ]]; then continue; fi

    echo "---------------------------------------------------"
    echo "[INFO] updating file: ${fname}"
    chmod u+w "$f"

    # Add response import after 'from reports_api.openapi_server import util'
    sed -i '' "/from reports_api.openapi_server import util/{
a\\
from reports_api.response_code import ${fname%.py} as rc
}" "$f"

    # Replace 'do some magic!' with corresponding rc.function call
    while read -r line; do
        if [[ $line == def* ]]; then
            func_name=$(echo "$line" | cut -d ':' -f 1 | cut -d ' ' -f 2-)
            clean_name=${func_name//=None/}
            echo "  - $clean_name"
            sed -i '' "0,/'do some magic!'/s//rc.${clean_name}/" "$f"
        fi
    done < "$f"
done

echo "[INFO] completed - check files prior to use"
cd "$SCRIPTS_DIR" || exit 0
