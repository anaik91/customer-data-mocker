from flask import request, jsonify # Still use Flask's request/jsonify helpers
import functions_framework
import datetime
import json
from typing import Dict, Any, Literal, Tuple, Optional # Keep Tuple, Optional

# Assuming 'models.py' exists and contains generate_customer_data
from models import generate_customer_data

# --- Data Generation (Keep as is) ---
NUM_PROFILES_TO_GENERATE = 20
RANDOM_SEED = 123
print(f"Generating {NUM_PROFILES_TO_GENERATE} customer profiles...")
customer_data = generate_customer_data(NUM_PROFILES_TO_GENERATE, seed=RANDOM_SEED)
print("Customer profile generation complete.") # Added confirmation

# --- Data Access Functions (Keep as is) ---
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

def find_purchase_and_item(transaction_id: str, item_id: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Searches customer_data for a specific transaction and item.
    Returns: A tuple containing (purchase_dict, item_dict) if both found,
             (purchase_dict, None) if transaction found but item not,
             None if transaction not found.
    """
    print(f"Searching for transaction_id='{transaction_id}', item_id='{item_id}'")
    for profile in customer_data:
        for purchase in profile.get("recent_purchases", []):
            if purchase.get("transaction_id") == transaction_id:
                for item in purchase.get("items", []):
                    # IMPORTANT: Match the item_id structure (might have suffix)
                    # Assuming item_id in data might be like "ITEM_TV_S_abcd"
                    # and the input item_id might be just "ITEM_TV_S" or the full ID.
                    # Let's use 'startswith' for flexibility, or adjust if exact match needed.
                    if item.get("item_id", "").startswith(item_id): # Use startswith or == based on expected input
                        print("Found matching purchase and item.")
                        return purchase, item # Return both purchase and the specific item dict
                print(f"Transaction '{transaction_id}' found, but item matching '{item_id}' not found within it.")
                return purchase, None # Transaction found, but item ID didn't match any items within it
    print(f"Transaction '{transaction_id}' not found.")
    return None # Transaction ID itself was not found

# --- Return Analysis Logic (Keep these functions separate if needed elsewhere, but they won't be called by the modified route) ---
# Keep ValidReturnReason etc. if used by other routes or potentially future routes
ReturnType = Literal["Allow Keep", "Allow Return", "Require Chat"]
ValidReturnReason = Literal["missing", "wrong_address", "shattered", "food_non_baby", "food_baby", "other"]
ValidCounterActResponse = Literal["allow", "disallow", "review"]

def is_highly_abused(item_dict: Dict[str, Any]) -> bool:
    # ... (keep implementation as is) ...
    item_name = item_dict.get("item_name", "").lower()
    category = item_dict.get("category", "").lower()
    if "funko" in item_name: return True
    if category == "baby" and "food" in item_name: return True
    if category == "limited time offer" or "lto" in item_name: return True
    if category == "baby food": return True
    return False

def _apply_return_flowchart_logic(
    item_dict: Dict[str, Any],
    return_reason: ValidReturnReason,
    total_transaction_value: float,
    counter_act_response: ValidCounterActResponse
) -> Dict[str, Any]:
    # ... (keep implementation as is) ...
    print(f"Applying flowchart logic for item: {item_dict.get('item_name', 'N/A')}, Reason: {return_reason}, Total TX Val: ${total_transaction_value:.2f}, CA: {counter_act_response}")
    item_price = item_dict.get("price", 0.0) * item_dict.get("quantity", 1)
    item_is_highly_abused = is_highly_abused(item_dict)
    is_missing_wrong_address_non_baby_food = return_reason in ["missing", "wrong_address", "food_non_baby"]

    if is_missing_wrong_address_non_baby_food:
        if item_is_highly_abused: outcome: ReturnType = "Require Chat"; msg = "Highly abused or baby item reported missing/wrong address/non-baby food."
        else:
            if total_transaction_value > 50:
                if counter_act_response == 'allow': outcome = "Allow Keep"; msg = f"Return (TX Val >$50): Item missing/etc. CounterAct allows."
                else: outcome = "Require Chat"; msg = f"Return (TX Val >$50): Item missing/etc. Requires review due to CounterAct ({counter_act_response})."
            else: outcome = "Allow Keep"; msg = f"Return (TX Val <=$50): Item missing/etc."
    else:
        if item_is_highly_abused: outcome = "Allow Return"; msg = "Item is highly abused and not reported missing/etc."
        else:
            if return_reason == "shattered":
                if item_price > 30:
                    if counter_act_response == 'allow': outcome = "Allow Keep"; msg = f"Shattered Item (>${item_price:.2f} > $30). CounterAct allows."
                    else: outcome = "Require Chat"; msg = f"Shattered Item (>${item_price:.2f} > $30). Requires review due to CounterAct ({counter_act_response})."
                else: outcome = "Allow Keep"; msg = f"Shattered Item (<=${item_price:.2f} <= $30)."
            else:
                if total_transaction_value > 30: outcome = "Allow Return"; msg = f"Return (TX Val >$30): Item not highly abused, not shattered/missing/etc."
                else:
                    if counter_act_response == 'allow': outcome = "Allow Keep"; msg = f"Return (TX Val <=$30): Item not highly abused/etc. CounterAct allows."
                    else: outcome = "Allow Return"; msg = f"Return (TX Val <=$30): Item not highly abused/etc., but CounterAct requires return ({counter_act_response})."

    print(f"Flowchart Outcome: {outcome}, Message: {msg}")
    return {"outcome": outcome, "reason_message": msg}


def analyze_return_by_transaction(
    transaction_id: str, item_id: str, return_reason: ValidReturnReason, counter_act_response: ValidCounterActResponse
) -> Dict[str, Any]:
    # --- This function is NO LONGER CALLED by the modified route, ---
    # --- but kept here in case it's used elsewhere.             ---
    print("--- (Full Analysis Function Called - Not Expected for Basic Find Route) ---")
    found_data = find_purchase_and_item(transaction_id, item_id)
    if not found_data: return {"error": "Transaction not found", "transaction_id": transaction_id, "status_code": 404}
    purchase_dict, item_dict = found_data
    if not item_dict: return {"error": "Item not found within transaction", "transaction_id": transaction_id, "item_id": item_id, "status_code": 404}

    total_transaction_value = purchase_dict.get("total_amount", 0.0)
    try:
        analysis_result = _apply_return_flowchart_logic(
            item_dict=item_dict, return_reason=return_reason, total_transaction_value=total_transaction_value, counter_act_response=counter_act_response
        )
        return analysis_result
    except Exception as e:
        print(f"Error applying flowchart logic: {e}")
        return {"error": "Internal error during return analysis.", "status_code": 500}


# --- Helper for Literal Validation (Keep if needed for other routes) ---
import sys
if sys.version_info >= (3, 8):
    from typing import get_args
else:
    def get_args(tp): return getattr(tp, '__args__', ())


# --- Cloud Function Entry Point (MODIFIED) ---

@functions_framework.http
def customer_api_conditional(request):
    """ HTTP Cloud Function endpoint. """
    path = request.path
    method = request.method
    print(f"Request path: {path}, Method: {method}")

    # === ROUTE: /returns/analyze_by_tx (MODIFIED BEHAVIOR) ===
    # This route now ONLY FINDS the transaction and item, it DOES NOT analyze return reasons.
    if path == '/returns/analyze_by_tx':
        if method == 'POST':
            json_data = request.get_json(silent=True)
            if not json_data: return jsonify({"error": "Invalid or missing JSON request body."}), 400

            # **MODIFIED: Only require transaction_id and item_id**
            required_fields = ["transaction_id", "item_id"]
            missing_fields = [field for field in required_fields if field not in json_data]
            if missing_fields: return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

            transaction_id = json_data.get("transaction_id")
            item_id = json_data.get("item_id")

            # **MODIFIED: Validate only transaction_id and item_id**
            if not isinstance(transaction_id, str) or not transaction_id: return jsonify({"error": "'transaction_id' must be a non-empty string."}), 400
            if not isinstance(item_id, str) or not item_id: return jsonify({"error": "'item_id' must be a non-empty string."}), 400

            # **MODIFIED: Directly call find_purchase_and_item**
            found_data = find_purchase_and_item(transaction_id, item_id)

            # **MODIFIED: Handle results from find_purchase_and_item**
            if found_data is None:
                # Transaction ID itself was not found
                return jsonify({"error": "Transaction not found", "transaction_id": transaction_id}), 404
            else:
                purchase_dict, item_dict = found_data
                if item_dict is None:
                    # Transaction was found, but the item_id didn't match any item within it
                    return jsonify({
                        "error": "Item not found within the specified transaction",
                        "transaction_id": transaction_id,
                        "item_id_searched": item_id
                        #"purchase_found": purchase_dict # Optionally include purchase data even if item missing
                    }), 404
                else:
                    # Both transaction and item were found successfully
                    return jsonify({
                        "message": "Transaction and item found.",
                        "purchase": purchase_dict,
                        "item": item_dict
                    }), 200

        else: return jsonify({"error": "Method Not Allowed. Use POST."}), 405

    # === Other Routes (Keep as is, or modify if needed) ===
    elif path == '/users':
        if method == 'POST':
            json_data = request.get_json(silent=True)
            if not json_data: return jsonify({"error": "Invalid or missing JSON request body."}), 400
            email_param = json_data.get("email")
            if not email_param or not isinstance(email_param, str):
                 return jsonify({"error": "'email' must be a non-empty string in the JSON body."}), 400

            found_customer = get_customer_data_by_email(email_param)
            if found_customer:
                return jsonify(found_customer), 200 # OK
            else:
                return jsonify({"error": "Customer not found for the provided email", "email": email_param}), 404 # Not Found
        else: return jsonify({"error": "Method Not Allowed. Use POST."}), 405

    elif path == '/list_emails':
        if method == 'GET': return jsonify(get_all_emails()), 200
        else: return jsonify({"error": f"Method Not Allowed for {path}. Use GET."}), 405

    elif path == '/':
        if method == 'GET':
            return jsonify({
               "message": "Welcome to the Customer API (Conditional Routing)",
               "endpoints": {
                   "GET /": "Get API information.",
                   "POST /users": "Get specific customer profile by email (JSON body: {'email': 'user@example.com'}).",
                   "GET /list_emails": "Get a list of all unique customer emails.",
                   "POST /returns/analyze_by_tx": "Find transaction and item data (JSON body: {'transaction_id': '...', 'item_id': '...'})."
                   # Add back full analysis endpoint description if you create one
               }
            }), 200
        else: return jsonify({"error": f"Method Not Allowed for {path}. Use GET."}), 405
    else:
        return jsonify({"error": f"Not Found: Path '{path}' not found."}), 404

# --- Local Development Runner (Keep as is) ---
if __name__ == '__main__':
    # Note: This block doesn't run when deployed to Cloud Functions.
    # Use the functions-framework CLI for local testing.
    print("--- Local Development Mode ---")
    print("This script defines the Cloud Function.")
    print("To run locally for testing, use the command:")
    print("functions-framework --target customer_api_conditional --debug --port 8080")
    print("-----------------------------")
    # You could add code here to simulate a request for very basic testing,
    # but using functions-framework is recommended for full HTTP simulation.