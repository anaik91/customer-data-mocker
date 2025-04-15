#!/bin/bash

# === Configuration ===
CONFIG_FILE="config.ini" # Name of the configuration file

# === Helper Function to Read INI ===
# Usage: read_ini <key> <default_value>
read_ini() {
  local key="$1"
  local default_value="${2:-}"
  local value=$(grep -E "^\s*${key}\s*=" "$CONFIG_FILE" 2>/dev/null | \
                grep -vE "^\s*(#|;|$)" | \
                sed -e 's/^[^=]*=\s*//' -e 's/\s*$//' -e 's/^\s*//' | \
                head -n 1)
  if [[ -n "$value" ]]; then echo "$value"; else echo "$default_value"; fi
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

# === Test Setup ===
# Colors for output
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'; NC='\033[0m'
# Counters
tests_run=0; tests_passed=0; tests_failed=0

# Helper function for printing test results
run_test() {
    local description="$1"; local method="$2"; local path="$3"; local expected_status="$4"; local curl_args="$5"
    ((tests_run++)); echo -n "Test: ${description} (${method} ${path})... "
    local full_url="${BASE_URL}${path}"; local status_code; local output_file=$(mktemp)
    status_code=$(curl --silent --show-error --fail --location --write-out "%{http_code}" --output "$output_file" -X "${method}" ${curl_args} "${full_url}" 2>/dev/null)
    local curl_exit_code=$?
    if [[ $curl_exit_code -ne 0 && $curl_exit_code -ne 22 ]]; then if [[ -z "$status_code" || "$status_code" == "000" ]]; then status_code="CURL Error ${curl_exit_code}"; fi; fi
    if [[ "$status_code" == "$expected_status" ]]; then echo -e "${GREEN}PASS${NC} (Status: ${status_code})"; ((tests_passed++)); else echo -e "${RED}FAIL${NC} (Expected: ${expected_status}, Got: ${status_code})"; ((tests_failed++)); fi
    rm "$output_file"
}

# === Pre-checks ===
echo "--- Running Pre-checks ---"
command -v gcloud >/dev/null 2>&1 || { echo >&2 "ERROR: gcloud command not found."; exit 1; }
command -v curl >/dev/null 2>&1 || { echo >&2 "ERROR: curl command not found."; exit 1; }
command -v jq >/dev/null 2>&1 || { echo >&2 "ERROR: jq command not found."; exit 1; }
echo "All necessary commands found."

# === Fetch Function URL ===
echo "--- Fetching Function URL for '${FUNCTION_NAME}' in region '${REGION}' ---"
BASE_URL=$(gcloud functions describe "${FUNCTION_NAME}" --region="${REGION}" --format='value(url)' 2>/dev/null)

if [[ -z "$BASE_URL" ]]; then
    echo >&2 "ERROR: Failed to retrieve URL for function '${FUNCTION_NAME}' in region '${REGION}'."
    echo >&2 "Please ensure the function is deployed and the name/region in ${CONFIG_FILE} are correct."
    exit 1
fi
BASE_URL=$(echo "${BASE_URL}" | sed 's:/*$::') # Remove trailing slash if present
echo "Function URL: ${BASE_URL}"

# === Running API Tests ===
echo "--- Running API Tests ---"
run_test "Root Endpoint" "GET" "/" "200"
run_test "List All Emails" "GET" "/list_emails" "200"
run_test "Get All Users" "GET" "/users" "200"

echo -n "Test: Get Specific User (Valid Email)... "
((tests_run++)); email_list_json=$(curl --silent --show-error --fail --location -X GET "${BASE_URL}/list_emails");
if [[ $? -ne 0 || -z "$email_list_json" ]]; then echo -e "${YELLOW}SKIP${NC} (Could not fetch email list)"; else
    valid_email=$(echo "$email_list_json" | jq -r '.[0] // empty');
    if [[ -z "$valid_email" ]]; then echo -e "${YELLOW}SKIP${NC} (Email list empty)"; else
        echo -n "(Using: ${valid_email})... "; status_code=$(curl --silent --show-error --fail --location -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/users?email=${valid_email}"); curl_exit_code=$?
        if [[ $curl_exit_code -ne 0 && $curl_exit_code -ne 22 ]]; then if [[ -z "$status_code" || "$status_code" == "000" ]]; then status_code="CURL Error ${curl_exit_code}"; fi; fi
        if [[ "$status_code" == "200" ]]; then echo -e "${GREEN}PASS${NC} (Status: ${status_code})"; ((tests_passed++)); else echo -e "${RED}FAIL${NC} (Expected: 200, Got: ${status_code})"; ((tests_failed++)); fi
    fi
fi

invalid_email="nonexistent-user-$(date +%s)@example.com"
run_test "Get Specific User (Invalid Email)" "GET" "/users?email=${invalid_email}" "404"
run_test "Invalid Path" "GET" "/invalid_random_path_123" "404"
run_test "Invalid Method (POST /users)" "POST" "/users" "405" "" "-d {}"

# === Test Summary ===
echo "--- Test Summary ---"
echo "Total Tests Run: ${tests_run}"; echo -e "Passed: ${GREEN}${tests_passed}${NC}"; echo -e "Failed: ${RED}${tests_failed}${NC}"; echo "--------------------"
if [[ ${tests_failed} -gt 0 ]]; then exit 1; else exit 0; fi