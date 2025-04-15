from flask import request, jsonify # Still use Flask's request/jsonify helpers
import functions_framework
import datetime
import json
from typing import Dict, Any, Literal, Tuple, Optional # Added Tuple, Optional

# Assuming 'models.py' exists and contains generate_customer_data
# from models import generate_customer_data, Item # Import Item if needed
from models import generate_customer_data

# --- Data Generation ---
NUMBER_TO_GENERATE = 20
print(f"Generating {NUMBER_TO_GENERATE} customer profiles...")
customer_data = generate_customer_data(NUMBER_TO_GENERATE)
print("Customer data generated.")

# --- Data Access Functions ---

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
    Returns: A tuple containing (purchase_dict, item_dict or None) if transaction found, otherwise None.
    """
    print(f"Searching for transaction_id='{transaction_id}', item_id='{item_id}'")
    for profile in customer_data:
        for purchase in profile.get("recent_purchases", []):
            if purchase.get("transaction_id") == transaction_id:
                for item in purchase.get("items", []):
                    if item.get("item_id") == item_id:
                        print("Found matching purchase and item.")
                        return purchase, item
                print(f"Transaction '{transaction_id}' found, but item '{item_id}' not found within it.")
                return purchase, None # Item not found within the correct transaction
    print(f"Transaction '{transaction_id}' not found.")
    return None # Transaction not found

# --- Return Analysis Logic ---

ReturnType = Literal["Allow Keep", "Allow Return", "Require Chat"]
ValidReturnReason = Literal["missing", "wrong_address", "shattered", "food_non_baby", "food_baby", "other"]
ValidCounterActResponse = Literal["allow", "disallow", "review"]

def is_highly_abused(item_dict: Dict[str, Any]) -> bool:
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


# --- Helper for Literal Validation (Python 3.8+) ---
# MOVED THIS BLOCK *BEFORE* customer_api_conditional
import sys
if sys.version_info >= (3, 8):
    from typing import get_args
else:
    # Basic fallback for older versions
    def get_args(tp):
        return getattr(tp, '__args__', ())


# --- Cloud Function Entry Point ---

@functions_framework.http
def customer_api_conditional(request):
    """ HTTP Cloud Function endpoint. """
    path = request.path
    method = request.method
    print(f"Request path: {path}, Method: {method}")

    # === ROUTE: /returns/analyze_by_tx ===
    if path == '/returns/analyze_by_tx':
        if method == 'POST':
            json_data = request.get_json(silent=True)
            if not json_data: return jsonify({"error": "Invalid or missing JSON request body."}), 400

            required_fields = ["transaction_id", "item_id", "return_reason", "counter_act_response"]
            missing_fields = [field for field in required_fields if field not in json_data]
            if missing_fields: return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

            transaction_id = json_data.get("transaction_id"); item_id = json_data.get("item_id")
            return_reason = json_data.get("return_reason"); counter_act_response = json_data.get("counter_act_response")

            if not isinstance(transaction_id, str) or not transaction_id: return jsonify({"error": "'transaction_id' must be a non-empty string."}), 400
            if not isinstance(item_id, str) or not item_id: return jsonify({"error": "'item_id' must be a non-empty string."}), 400
            # Now get_args is defined
            if return_reason not in get_args(ValidReturnReason): return jsonify({"error": f"'return_reason' must be one of: {get_args(ValidReturnReason)}"}), 400
            if counter_act_response not in get_args(ValidCounterActResponse): return jsonify({"error": f"'counter_act_response' must be one of: {get_args(ValidCounterActResponse)}"}), 400

            result = analyze_return_by_transaction(transaction_id=transaction_id, item_id=item_id, return_reason=return_reason, counter_act_response=counter_act_response)

            if "error" in result:
                status_code = result.get("status_code", 500)
                error_response = {k: v for k, v in result.items() if k != 'status_code'}
                return jsonify(error_response), status_code
            else:
                return jsonify(result), 200
        else: return jsonify({"error": "Method Not Allowed. Use POST."}), 405

    # === Other Routes (GET /users, GET /list_emails, GET /) ===
    elif path == '/users':
        if method == 'GET': return jsonify(customer_data), 200 # Simplified for brevity
        else: return jsonify({"error": f"Method Not Allowed for {path}"}), 405
    elif path == '/list_emails':
        if method == 'GET': return jsonify(get_all_emails()), 200
        else: return jsonify({"error": f"Method Not Allowed for {path}"}), 405
    elif path == '/':
        if method == 'GET':
            return jsonify({
               "message": "Welcome to the Customer API (Conditional Routing)",
               "endpoints": {
                   "GET /": "Get API information.",
                   "GET /users": "Get all customer profiles.",
                   "GET /list_emails": "Get a list of all unique customer emails.",
                   "POST /returns/analyze_by_tx": "Analyze a return request by transaction/item ID (JSON body: transaction_id, item_id, return_reason, counter_act_response)."
               }
            }), 200
        else: return jsonify({"error": f"Method Not Allowed for {path}"}), 405
    else:
        return jsonify({"error": f"Not Found: Path '{path}' not found."}), 404

# --- Local Development Runner ---
if __name__ == '__main__':
    print("Use: functions-framework --target customer_api_conditional --debug")