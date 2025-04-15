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
RUNTIME=$(read_ini "runtime" "python312") # Default if not in ini
ENTRY_POINT=$(read_ini "entry_point")
SOURCE_DIR=$(read_ini "source_dir" ".") # Default if not in ini
ALLOW_UNAUTHENTICATED=$(read_ini "allow_unauthenticated" "false") # Default to false (secure)
MEMORY=$(read_ini "memory" "256MiB") # Default if not in ini
TIMEOUT=$(read_ini "timeout" "60s") # Default if not in ini

# --- Validate REQUIRED Configuration ---
if [[ -z "$FUNCTION_NAME" ]]; then echo "ERROR: 'name' not set in ${CONFIG_FILE}"; exit 1; fi
if [[ -z "$REGION" ]]; then echo "ERROR: 'region' not set in ${CONFIG_FILE}"; exit 1; fi
if [[ -z "$ENTRY_POINT" ]]; then echo "ERROR: 'entry_point' not set in ${CONFIG_FILE}"; exit 1; fi
if [[ -z "$RUNTIME" ]]; then echo "ERROR: 'runtime' not set in ${CONFIG_FILE} and no default provided."; exit 1; fi

# Determine the authentication flag based on the variable
if [[ "$ALLOW_UNAUTHENTICATED" == "true" ]]; then
  AUTH_FLAG="--allow-unauthenticated"
  AUTH_DESC="Public (Unauthenticated)"
else
  AUTH_FLAG="--no-allow-unauthenticated"
  AUTH_DESC="IAM Authenticated Only"
fi

# Check source directory and files (using read SOURCE_DIR)
if [ ! -d "$SOURCE_DIR" ]; then echo "ERROR: Source directory '$SOURCE_DIR' not found."; exit 1; fi
ENTRY_FILE="${SOURCE_DIR}/main.py" # Assuming entry point is always in main.py
if [ ! -f "$ENTRY_FILE" ]; then echo "ERROR: Entry point file '$ENTRY_FILE' not found in source directory."; exit 1; fi
REQUIREMENTS_FILE="${SOURCE_DIR}/requirements.txt"
if [ ! -f "$REQUIREMENTS_FILE" ]; then echo "ERROR: Requirements file '$REQUIREMENTS_FILE' not found in source directory."; exit 1; fi


# --- Display Plan ---
echo "--- Planning Deployment ---"
echo "Function Name:   ${FUNCTION_NAME}"
echo "Region:          ${REGION}"
echo "Runtime:         ${RUNTIME}"
echo "Entry Point:     ${ENTRY_POINT}"
echo "Source Dir:      ${SOURCE_DIR}"
echo "Memory:          ${MEMORY}"
echo "Timeout:         ${TIMEOUT}"
echo "Authentication:  ${AUTH_DESC}"
echo "---------------------------"
read -p "Proceed with deployment? (y/N): " confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || exit 1


# --- Execute Deployment ---
echo "Starting deployment..."

gcloud functions deploy "${FUNCTION_NAME}" \
    --runtime "${RUNTIME}" \
    --trigger-http \
    --entry-point "${ENTRY_POINT}" \
    --source "${SOURCE_DIR}" \
    --region "${REGION}" \
    --memory "${MEMORY}" \
    --timeout "${TIMEOUT}" \
    "${AUTH_FLAG}" # This correctly inserts either --allow or --no-allow flag

# Check the exit status of the gcloud command
EXIT_STATUS=$?
if [ ${EXIT_STATUS} -ne 0 ]; then
  echo "ERROR: gcloud deployment failed with exit status ${EXIT_STATUS}."
  exit ${EXIT_STATUS}
else
  echo "--- Deployment successful! ---"
  echo "Fetching trigger URL..."
  TRIGGER_URL=$(gcloud functions describe "${FUNCTION_NAME}" --region="${REGION}" --format='value(url)' 2>/dev/null)
  if [ -n "$TRIGGER_URL" ]; then
      echo "Trigger URL: ${TRIGGER_URL}"
  else
      echo "Could not automatically fetch trigger URL. Check the Google Cloud Console."
  fi
fi

exit 0