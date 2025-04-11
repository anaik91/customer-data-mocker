
## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    # git clone <your-repository-url>
    # cd <repository-directory>
    ```

2.  **Create Configuration (`config.ini`):**
    *   **This step is required.** Create a file named `config.ini` in the project root.
    *   Populate it with the following structure, **editing the values** (especially `name` and `region`) according to your needs:
        ```ini
        # Configuration for Cloud Function Deployment and Testing
        [Function]
        # REQUIRED: Name for the deployed Cloud Function
        name=customer-api

        # REQUIRED: GCP region for deployment
        region=us-central1

        # REQUIRED: Python runtime version (e.g., python39, python310, python311, python312)
        runtime=python312

        # REQUIRED: Function name in main.py to execute
        entry_point=customer_api

        # Directory containing source code (usually .)
        source_dir=.

        # Set to true for public access, false for IAM-only
        allow_unauthenticated=true

        # OPTIONAL: Function memory allocation
        memory=256MiB

        # OPTIONAL: Function execution timeout
        timeout=60s
        ```

3.  **Create Virtual Environment:** (Recommended for isolating dependencies)
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Local Development and Testing

You can run the function locally to simulate the Cloud Functions environment using the `functions-framework`. This allows for faster iteration without deploying to GCP.

1.  **Run Locally:**
    *   Make sure your virtual environment is activated (`source venv/bin/activate`).
    *   Execute the following command from the project's root directory:
        ```bash
        functions-framework --target customer_api_conditional --debug
        ```
        *(Ensure `--target` matches the `entry_point` value in your `config.ini` and the function name decorated with `@functions_framework.http` in `main.py`)*
    *   The framework will start a local web server, typically listening on `http://localhost:8080`. You'll see log output indicating the server is running and the mock data is being generated.

2.  **Test Locally:**
    *   Open your web browser or use a tool like `curl` to access the local endpoints:
        ```bash
        # Get API info
        curl http://localhost:8080/

        # Get all users
        curl http://localhost:8080/users

        # Get list of emails
        curl http://localhost:8080/list_emails

        # Get a specific user (replace with an actual email from the generated list)
        # First get emails: curl http://localhost:8080/list_emails | jq .
        # Then use one: curl "http://localhost:8080/users?email=some.generated.email@example.com"
        # Test not found: curl -i "http://localhost:8080/users?email=nonexistent@example.com" # -i shows headers including 404 status
        ```

## Deployment to Google Cloud Functions

The provided `deploy_function.sh` script automates the deployment process using `gcloud` and reads settings from `config.ini`.

1.  **Ensure Configuration:** Double-check that `config.ini` has the correct `name`, `region`, `runtime`, `entry_point` and other settings for your target deployment.
2.  **Make Script Executable:** (Run this once)
    ```bash
    chmod +x deploy_function.sh
    ```
3.  **Run Deployment Script:**
    ```bash
    ./deploy_function.sh
    ```
    *   The script will display the planned configuration read from `config.ini`.
    *   It will ask for confirmation (`y/N`) before proceeding.
    *   It executes `gcloud functions deploy` with the configured parameters.
    *   Upon successful deployment, it will attempt to display the function's HTTPS trigger URL.

4.  **(Alternative) Manual Deployment:** You can always deploy directly using `gcloud`, substituting your own values:
    ```bash
    gcloud functions deploy YOUR_FUNCTION_NAME \
        --runtime YOUR_RUNTIME \
        --trigger-http \
        --entry-point YOUR_ENTRY_POINT \
        --source . \
        --region YOUR_REGION \
        --allow-unauthenticated # Or --no-allow-unauthenticated
    ```

5.  **`.gcloudignore`:** This file ensures that unnecessary files (like the `venv/` directory, test scripts, local config, etc.) are not included in the deployment package uploaded to GCP. This keeps the deployment artifact small and clean. You can customize it further if needed.

## Testing the Deployed Function

After deployment, you can use the `test.sh` script to verify the function's endpoints are working correctly on GCP.

1.  **Ensure Configuration:** Make sure `config.ini` contains the correct `name` and `region` of the function you *just deployed* or want to test.
2.  **Make Script Executable:** (Run this once)
    ```bash
    chmod +x test.sh
    ```
3.  **Run Test Script:**
    ```bash
    ./test.sh
    ```
    *   The script requires `gcloud`, `curl`, and `jq`.
    *   It fetches the deployed function's HTTPS trigger URL using `gcloud functions describe`.
    *   It runs `curl` commands against the live endpoints (`/`, `/users`, `/list_emails`, `/users?email=...`).
    *   It checks the HTTP status codes of the responses.
    *   It reports PASS/FAIL status for each test and provides a final summary.
    *   The script exits with status code `0` if all tests pass, or `1` if any test fails (useful for CI/CD pipelines).

## Configuration (`config.ini`) Reference

This file centralizes settings used by the deployment and testing scripts.

```ini
# Configuration for Cloud Function Deployment and Testing

[Function]
# REQUIRED: Name for the deployed Cloud Function
name=customer-api

# REQUIRED: GCP region for deployment
region=us-central1

# REQUIRED: Python runtime version (e.g., python39, python310, python311, python312)
runtime=python312

# REQUIRED: Function name in main.py to execute
entry_point=customer_api

# Directory containing source code (usually .)
source_dir=.

# Set to true for public access, false for IAM-only
allow_unauthenticated=true

# OPTIONAL: Function memory allocation
memory=256MiB

# OPTIONAL: Function execution timeout
timeout=60s
```