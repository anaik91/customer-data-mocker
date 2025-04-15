#!/bin/bash

# === Configuration ===
CONFIG_FILE="config.ini" # Name of the configuration file

# === Helper Function to Read INI ===
# Usage: read_ini <key> <default_value>
# Reads from the [Function] section implicitly
read_ini() {
  local key="$1"
  local default_value="${2:-}" # Use provided default or empty string
  # 1. Grep the line: ^optional_space key optional_space = optional_space value optional_space$
  # 2. Filter out comments (lines starting with # or ;) and empty lines
  # 3. Remove everything up to the first '='
  # 4. Remove leading/trailing whitespace from the result
  # 5. Take the first match found
  local value=$(grep -E "^\s*${key}\s*=" "$CONFIG_FILE" 2>/dev/null | \
                grep -vE "^\s*(#|;|$)" | \
                sed -e 's/^[^=]*=\s*//' -e 's/\s*$//' -e 's/^\s*//' | \
                head -n 1)

  if [[ -n "$value" ]]; then
    echo "$value"
  else
    echo "$default_value"
  fi
}

# === Read Configuration from INI ===
echo "Reading configuration from ${CONFIG_FILE}..."

if [ ! -f "$CONFIG_FILE" ]; then
  echo "ERROR: Configuration file '${CONFIG_FILE}' not found."
  exit 1
fi

FUNCTION_NAME=$(read_ini "name")
REGION=$(read_ini "region")

# --- Validate REQUIRED Configuration ---
if [[ -z "$FUNCTION_NAME" ]]; then echo "ERROR: 'name' not set in ${CONFIG_FILE}"; exit 1; fi
if [[ -z "$REGION" ]]; then echo "ERROR: 'region' not set in ${CONFIG_FILE}"; exit 1; fi

# --- Display Plan ---
echo "--- Planning cleanup ---"
echo "Function Name:   ${FUNCTION_NAME}"
echo "Region:          ${REGION}"
echo "---------------------------"
read -p "Proceed with cleanup? (y/N): " confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || exit 1


# --- Execute Deployment ---
echo "Starting cleanup..."

gcloud functions delete "${FUNCTION_NAME}" \
    --region "${REGION}"
