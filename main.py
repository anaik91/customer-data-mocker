from flask import request, jsonify # Still use Flask's request/jsonify helpers
import functions_framework
import datetime
import json

# Assuming 'models.py' exists in the same directory and contains
# the generate_customer_data function and the necessary data classes.
from models import generate_customer_data

# --- Data Generation ---
# Generate data once per function instance lifecycle (on cold start)
NUMBER_TO_GENERATE = 20
print(f"Generating {NUMBER_TO_GENERATE} customer profiles...")
customer_data = generate_customer_data(NUMBER_TO_GENERATE)
print("Customer data generated.")

# --- Data Access Functions (Keep these as they are) ---

def get_customer_data_by_email(email_to_find: str):
    """Finds a customer profile dictionary by matching the email address."""
    if not email_to_find: return None
    print(f"Searching for email: {email_to_find}")
    for customer_profile in customer_data:
        if customer_profile.get("customer", {}).get("email") == email_to_find:
            print(f"Found customer profile for email: {email_to_find}")
            return customer_profile
    print(f"Email not found: {email_to_find}")
    return None

def get_all_customer_data():
    """Returns the full list of customer profile dictionaries."""
    print("Returning all customer data.")
    return customer_data

def get_all_emails() -> list[str]:
    """Extracts and returns a list of all customer email addresses."""
    print("Extracting all customer emails.")
    emails = set()
    for customer_profile in customer_data:
        email = customer_profile.get("customer", {}).get("email")
        if email:
            emails.add(email)
    print(f"Found {len(emails)} unique emails.")
    return sorted(list(emails))

# --- Cloud Function Entry Point with Conditional Routing ---

@functions_framework.http
def customer_api(request):
    """
    HTTP Cloud Function endpoint with conditional routing based on request path.
    - GET /users : Returns all customer data or data for a specific email.
    - GET /list_emails : Returns a list of all customer emails.
    - GET / : Provides basic API info.
    """

    # --- METHOD CHECK ---
    if request.method != 'GET':
        return jsonify({"error": "Method not allowed. Use GET."}), 405 # Method Not Allowed

    # --- PATH-BASED ROUTING ---
    path = request.path
    print(f"Request path: {path}") # Log the path

    # Note: request.path includes the leading slash '/'

    if path == '/users':
        # Handle requests for customer user data
        email_param = request.args.get("email")

        if email_param:
            # Find specific customer by email
            found_customer = get_customer_data_by_email(email_param)
            if found_customer:
                return jsonify(found_customer), 200 # OK
            else:
                # Specific 404 for email not found
                return jsonify({"error": "Customer not found for the provided email", "email": email_param}), 404 # Not Found
        else:
            # Return all customers
            all_data = get_all_customer_data()
            return jsonify(all_data), 200 # OK

    elif path == '/list_emails':
        # Handle requests to list all emails
        all_emails = get_all_emails()
        return jsonify(all_emails), 200 # OK

    elif path == '/':
         # Root endpoint providing basic API info
         return jsonify({
            "message": "Welcome to the Customer API (Conditional Routing)",
            "endpoints": {
                "GET /users": "Get all customer profiles.",
                "GET /users?email=<email>": "Get profile for a specific email.",
                "GET /list_emails": "Get a list of all unique customer emails."
            }
         }), 200

    else:
        # --- INVALID PATH ---
        # Generic 404 for any other path
        return jsonify({"error": f"Not Found: The requested path '{path}' was not found."}), 404 # Not Found