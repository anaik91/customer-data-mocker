from flask import request, jsonify # Still use Flask's request/jsonify helpers
import functions_framework
import datetime
import json
from typing import Dict, Any, Literal, Tuple, Optional

# Import the data generator FROM YOUR models.py file!
# Make sure models.py contains the LATEST non-null/non-empty generator
try:
    from models import generate_customer_data
except ImportError:
    print("ERROR: Cannot import 'generate_customer_data' from 'models'. Ensure models.py exists and is correct.")
    # Provide a dummy function or raise error to prevent proceeding
    def generate_customer_data(num, seed=None): return []
    # raise # Or uncomment to stop execution if models is essential

# --- Data Generation ---
NUM_PROFILES_TO_GENERATE = 20
RANDOM_SEED = 123
print(f"Generating {NUM_PROFILES_TO_GENERATE} customer profiles...")
# Ensure the generator being called is the non-null/non-empty one
customer_data = generate_customer_data(NUM_PROFILES_TO_GENERATE, seed=RANDOM_SEED)
print("Customer profile generation complete.")

# --- Data Access Functions ---
def get_customer_data_by_email(email_to_find: str):
    if not email_to_find: return None
    print(f"Searching for email: {email_to_find}")
    for customer_profile in customer_data:
        if customer_profile.get("customer", {}).get("email") == email_to_find:
            print(f"Found customer profile for email: {email_to_find}")
            return customer_profile
    print(f"Email not found: {email_to_find}")
    return None

def get_all_emails() -> list[str]:
    print("Extracting all customer emails.")
    emails = set()
    for customer_profile in customer_data:
        email = customer_profile.get("customer", {}).get("email")
        if email and isinstance(email, str):
            emails.add(email)
    print(f"Found {len(emails)} unique emails.")
    return sorted(list(emails))


# --- Return Analysis Types ---
ValidReturnReason = Literal["missing", "wrong_address", "shattered", "food_non_baby", "food_baby", "other"]
AnalysisResult = Dict[Literal["isChat", "ReturnNeeded", "AutomatedReturn"], bool]

# --- Return Analysis Logic ---
def is_highly_abused(item_dict: Dict[str, Any]) -> bool:
    """Checks if an item is considered highly abused based on name/category."""
    item_name = item_dict.get("item_name", "Unknown Item").lower()
    category = item_dict.get("category", "General").lower()
    if "funko" in item_name: return True
    if category == "baby food": return True
    if category == "baby" and "food" in item_name: return True
    if category == "limited time offer": return True
    if "lto" in item_name: return True
    if "limited time offer" in item_name: return True
    return False

def _analyze_return_request(
    item_dict: Dict[str, Any],
    purchase_dict: Dict[str, Any],
    return_reason: ValidReturnReason
) -> AnalysisResult:
    """Applies the flowchart logic (excluding CounterAct) to determine return outcome."""
    print(f"Analyzing return: Item='{item_dict.get('item_name')}', Reason='{return_reason}', TX ID='{purchase_dict.get('transaction_id')}'")
    total_transaction_value = purchase_dict.get("total_amount", 0.01)
    item_price = item_dict.get("price", 0.01) * item_dict.get("quantity", 1)
    item_is_highly_abused = is_highly_abused(item_dict)
    is_baby_food_item = (item_dict.get("category", "").lower() == "baby food") or \
                        (item_dict.get("category", "").lower() == "baby" and "food" in item_dict.get("item_name", "").lower())
    is_missing_wrong_address = return_reason in ["missing", "wrong_address"]
    is_food_non_baby = return_reason == "food_non_baby"
    is_shattered = return_reason == "shattered"

    # --- Flowchart Logic Implementation ---
    if is_missing_wrong_address or is_food_non_baby:
        print("-> Path 1: Missing/Wrong Address/Food (Non-Baby)")
        if is_baby_food_item:
             print("-> Baby food reported missing/wrong address. Requires Chat.")
             return {"isChat": True, "ReturnNeeded": False, "AutomatedReturn": False}
        elif item_is_highly_abused:
            print("-> Highly abused item reported missing/wrong address/etc. Requires Chat.")
            return {"isChat": True, "ReturnNeeded": False, "AutomatedReturn": False}
        else:
            if total_transaction_value > 50:
                print(f"-> Not highly abused, TX Val (${total_transaction_value:.2f}) > $50. Requires Chat (No CounterAct).")
                return {"isChat": True, "ReturnNeeded": False, "AutomatedReturn": False}
            else: # <= $50
                print(f"-> Not highly abused, TX Val (${total_transaction_value:.2f}) <= $50. Guest can keep.")
                return {"isChat": False, "ReturnNeeded": False, "AutomatedReturn": True}
    else: # Other reasons (Shattered, Food (Baby), Other)
        print(f"-> Path 2: Reason is '{return_reason}'")
        if item_is_highly_abused:
            print("-> Highly abused item (or Baby Food reason). Return the item.")
            return {"isChat": False, "ReturnNeeded": True, "AutomatedReturn": True}
        else: # Not highly abused
            if is_shattered:
                print("-> Reason: Shattered")
                if item_price > 30:
                     print(f"-> Shattered item price (${item_price:.2f}) > $30. Requires Chat (No CounterAct).")
                     return {"isChat": True, "ReturnNeeded": False, "AutomatedReturn": False}
                else: # <= $30
                    print(f"-> Shattered item price (${item_price:.2f}) <= $30. Guest can keep.")
                    return {"isChat": False, "ReturnNeeded": False, "AutomatedReturn": True}
            else: # Not highly abused, Not MWAFNB, Not Shattered
                print(f"-> Reason: '{return_reason}' (Not Shattered/Missing/etc. & Not Highly Abused)")
                if total_transaction_value > 30:
                    print(f"-> TX Val (${total_transaction_value:.2f}) > $30. Return the item.")
                    return {"isChat": False, "ReturnNeeded": True, "AutomatedReturn": True}
                else: # <= $30
                    print(f"-> TX Val (${total_transaction_value:.2f}) <= $30. Return the item (No CounterAct).")
                    return {"isChat": False, "ReturnNeeded": True, "AutomatedReturn": True}

# Helper to find purchase and EXACT item ID
def find_purchase_and_item_exact(transaction_id: str, item_id: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Searches customer_data for a specific transaction and EXACT item ID."""
    print(f"Searching for transaction_id='{transaction_id}', exact item_id='{item_id}'")
    for profile in customer_data:
        customer_info = profile.get("customer", {})
        purchases = profile.get("recent_purchases", [])
        if not purchases: continue
        for purchase in purchases:
            if purchase.get("transaction_id") == transaction_id:
                items = purchase.get("items", [])
                if not items:
                    print(f"Transaction '{transaction_id}' found, but it has no items listed.")
                    return purchase, None
                for item in items:
                    if item.get("item_id") == item_id:
                        print("Found matching purchase and item.")
                        return purchase, item
                print(f"Transaction '{transaction_id}' found, but item '{item_id}' not found within it.")
                return purchase, None
    print(f"Transaction '{transaction_id}' not found across all profiles.")
    return None

# --- Helper for Literal Validation ---
# Place this before the function using it
import sys
if sys.version_info >= (3, 8):
    from typing import get_args
else:
    # Basic fallback for older versions
    def get_args(tp): return getattr(tp, '__args__', ())


# --- Cloud Function Entry Point ---
@functions_framework.http
def customer_api_conditional(request):
    """ HTTP Cloud Function endpoint. """
    path = request.path
    method = request.method
    print(f"Request path: {path}, Method: {method}")

    # === Route: /users (POST) ===
    if path == '/users':
        if method == 'POST':
            json_data = request.get_json(silent=True)
            if not json_data: return jsonify({"error": "Invalid or missing JSON request body."}), 400
            email_param = json_data.get("email")
            if not email_param or not isinstance(email_param, str):
                 return jsonify({"error": "'email' must be a non-empty string in the JSON body."}), 400
            found_customer = get_customer_data_by_email(email_param)
            if found_customer: return jsonify(found_customer), 200
            else: return jsonify({"error": "Customer not found for the provided email", "email": email_param}), 404
        else: return jsonify({"error": "Method Not Allowed. Use POST."}), 405

    # === Route: /list_emails (GET) ===
    elif path == '/list_emails':
        if method == 'GET': return jsonify(get_all_emails()), 200
        else: return jsonify({"error": f"Method Not Allowed for {path}. Use GET."}), 405

    # === NEW Route: /analyze_tx (POST) ===
    elif path == '/analyze_tx':
        if method == 'POST':
            json_data = request.get_json(silent=True)
            if not json_data: return jsonify({"error": "Invalid or missing JSON request body."}), 400

            # 1. Validate Input Fields
            required_fields = ["transaction_id", "item_id", "return_reason"]
            missing_fields = [field for field in required_fields if field not in json_data]
            if missing_fields: return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

            transaction_id = json_data.get("transaction_id")
            item_id = json_data.get("item_id")
            return_reason = json_data.get("return_reason")

            # Basic type validation
            if not isinstance(transaction_id, str) or not transaction_id: return jsonify({"error": "'transaction_id' must be a non-empty string."}), 400
            if not isinstance(item_id, str) or not item_id: return jsonify({"error": "'item_id' must be a non-empty string."}), 400
            # Validate return_reason against the Literal
            valid_reasons = get_args(ValidReturnReason)
            if return_reason not in valid_reasons:
                return jsonify({"error": f"'return_reason' must be one of: {valid_reasons}"}), 400

            # 2. Find the Purchase and Item
            found_data = find_purchase_and_item_exact(transaction_id, item_id)

            if found_data is None:
                return jsonify({"error": "Transaction not found", "transaction_id": transaction_id}), 404
            else:
                purchase_dict, item_dict = found_data
                if item_dict is None:
                    return jsonify({
                        "error": "Item not found within the specified transaction",
                        "transaction_id": transaction_id,
                        "item_id_searched": item_id
                    }), 404

            # 3. Apply the Analysis Logic
            try:
                analysis_result = _analyze_return_request(
                    item_dict=item_dict,
                    purchase_dict=purchase_dict,
                    return_reason=return_reason
                )
                # Return the specific boolean structure
                return jsonify(analysis_result), 200
            except Exception as e:
                # Catch potential errors during analysis
                print(f"ERROR during return analysis: {e}")
                return jsonify({"error": "Internal server error during return analysis."}), 500

        else:
            return jsonify({"error": "Method Not Allowed. Use POST."}), 405

    # === Route: / (GET) ===
    elif path == '/':
        if method == 'GET':
            return jsonify({
               "message": "Welcome to the Customer API (Conditional Routing)",
               "endpoints": {
                   "GET /": "Get API information.",
                   "POST /users": "Get specific customer profile by email (JSON body: {'email': 'user@example.com'}).",
                   "GET /list_emails": "Get a list of all unique customer emails.",
                   "POST /analyze_tx": "Analyze return request (JSON body: {'transaction_id': '...', 'item_id': '...', 'return_reason': '...'})."
               }
            }), 200
        else: return jsonify({"error": f"Method Not Allowed for {path}. Use GET."}), 405

    # === Handle Not Found Routes ===
    else:
        return jsonify({"error": f"Not Found: Path '{path}' not found."}), 404

# --- Local Development Runner ---
if __name__ == '__main__':
    print("--- Local Development Mode ---")
    print("This script defines the Cloud Function.")
    print("To run locally for testing, use the command:")
    print("functions-framework --target customer_api_conditional --debug --port 8080")
    print("-----------------------------")