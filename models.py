import datetime
import json
import random
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any  # Optional still useful for internal logic/from_dict
from faker import Faker

# --- Placeholders ---
PLACEHOLDER_DATE = "DATE_NOT_APPLICABLE"
PLACEHOLDER_TRACKING = "TRACKING_NOT_APPLICABLE"
PLACEHOLDER_CIRCLE_NUM = "CIRCLE_NUMBER_NOT_APPLICABLE"
PLACEHOLDER_ADDRESS_FIELD = "N/A" # Placeholder for address fields if needed by from_dict

# --- Class Definitions (Updated for Non-Empty) ---
@dataclass
class Address:
    # These are guaranteed non-empty by _create_random_address
    street_address: str = PLACEHOLDER_ADDRESS_FIELD
    city: str = PLACEHOLDER_ADDRESS_FIELD
    state: str = PLACEHOLDER_ADDRESS_FIELD
    zip_code: str = "00000" # Needs a valid-ish format placeholder

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, str]]) -> Optional['Address']:
        if data is None: return None
        # Basic creation, generator ensures non-empty
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class Preferences:
    # Generator ensures non-empty lists
    communication: List[str] = field(default_factory=lambda: ["email"]) # Default non-empty
    interests: List[str] = field(default_factory=lambda: ["general"]) # Default non-empty

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, List[str]]]) -> 'Preferences':
        if data is None: return cls() # Returns default non-empty lists
        # Ensure lists are non-empty if provided
        comm = data.get("communication", [])
        ints = data.get("interests", [])
        if not comm: comm = ["email"] # Fallback
        if not ints: ints = ["general"] # Fallback
        return cls(communication=comm, interests=ints)

@dataclass
class Item:
    # Generator ensures non-empty/non-zero
    item_id: str = "ITEM_UNKNOWN"
    item_name: str = "Unknown Item"
    category: str = "General"
    quantity: int = 1 # Default >= 1
    price: float = 0.01 # Default > 0

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Item']:
        if data is None: return None
        # Add validation/defaults if creating from potentially incomplete dict
        data.setdefault("item_id", "ITEM_UNKNOWN")
        data.setdefault("item_name", "Unknown Item")
        data.setdefault("category", "General")
        data.setdefault("quantity", 1)
        data.setdefault("price", 0.01)
        if data["quantity"] <= 0: data["quantity"] = 1
        if data["price"] <= 0: data["price"] = 0.01
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class Purchase:
    # Generator ensures non-empty/placeholders
    transaction_id: str = "TRANS_UNKNOWN"
    purchase_date: str = "DATE_UNKNOWN"
    delivered_date: str = PLACEHOLDER_DATE
    estimated_delivery_date: str = PLACEHOLDER_DATE
    store_id: str = "0000"
    store_name: str = "Unknown Store"
    items: List[Item] = field(default_factory=list)
    total_amount: float = 0.01 # Default > 0
    payment_method: str = "Unknown"
    order_type: str = "Unknown"
    shipping_address: Address = field(default_factory=Address) # Generator ensures populated Address
    tracking_number: str = PLACEHOLDER_TRACKING
    order_status: str = "Unknown"

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Purchase']:
        if data is None: return None
        # Add more robust validation/defaults if needed
        items_data = data.get("items", [])
        shipping_address_data = data.get("shipping_address")
        valid_data = {k: v for k, v in data.items() if k in cls.__annotations__}
        valid_data["items"] = [Item.from_dict(item_data) for item_data in items_data if item_data]
        address_obj = Address.from_dict(shipping_address_data)
        valid_data["shipping_address"] = address_obj if address_obj else Address() # Use default Address
        # Ensure required string fields are non-empty
        for key in ["transaction_id", "purchase_date", "store_id", "store_name", "payment_method", "order_type", "order_status"]:
             if not valid_data.get(key): valid_data[key] = "UNKNOWN" # Or specific placeholder
        # Ensure optional fields are non-empty or placeholder
        for key, placeholder in [("delivered_date", PLACEHOLDER_DATE), ("estimated_delivery_date", PLACEHOLDER_DATE), ("tracking_number", PLACEHOLDER_TRACKING)]:
             if not valid_data.get(key): valid_data[key] = placeholder
        if valid_data.get("total_amount", 0) <= 0 and valid_data["items"]: valid_data["total_amount"] = 0.01

        return cls(**valid_data)

@dataclass
class Recommendation:
    # Generator ensures non-empty
    item_id: str = "REC_ITEM_UNKNOWN"
    item_name: str = "Recommended Item"
    category: str = "General"
    reason: str = "Recommended for you"

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Recommendation']:
        if data is None: return None
        # Ensure non-empty on creation from dict
        data.setdefault("item_id", "REC_ITEM_UNKNOWN")
        data.setdefault("item_name", "Recommended Item")
        data.setdefault("category", "General")
        data.setdefault("reason", "Recommended for you")
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class Customer:
    # Generator ensures non-empty/placeholders
    customer_id: str = "CUST_UNKNOWN"
    first_name: str = "First"
    last_name: str = "Last"
    phone_number: str = "000-000-0000"
    email: str = "unknown@example.com"
    target_circle_member: bool = False
    target_circle_number: str = PLACEHOLDER_CIRCLE_NUM
    address: Address = field(default_factory=Address) # Generator ensures populated
    preferences: Preferences = field(default_factory=Preferences) # Generator ensures populated

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Customer']:
        if data is None: return None
        address_data = data.get("address")
        preferences_data = data.get("preferences")
        valid_data = {k: v for k, v in data.items() if k in cls.__annotations__}
        address_obj = Address.from_dict(address_data)
        valid_data["address"] = address_obj if address_obj else Address()
        valid_data["preferences"] = Preferences.from_dict(preferences_data) if preferences_data else Preferences()
        # Ensure required strings non-empty
        for key in ["customer_id", "first_name", "last_name", "phone_number", "email"]:
             if not valid_data.get(key): valid_data[key] = "UNKNOWN"
        # Ensure circle number non-empty
        if not valid_data.get("target_circle_number"): valid_data["target_circle_number"] = PLACEHOLDER_CIRCLE_NUM
        return cls(**valid_data)

# --- Data Generation Setup ---
fake = Faker()

# --- Constants ---
COMMUNICATION_PREFS = ["email", "text", "phone", "mail"]
INTERESTS = ["electronics", "home goods", "clothing", "groceries", "toys", "books", "sports", "outdoors", "beauty", "pharmacy", "baby", "pets", "entertainment"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "Cash", "Target Credit Card", "Gift Card", "PayPal"]
ORDER_TYPES = ["In-Store", "Online - Shipped", "Online - Pickup"]
ORDER_STATUS_SHIPPED = ["Processing", "Shipped", "In Transit", "Out for Delivery", "Delivered", "Delayed", "Cancelled"]
ORDER_STATUS_PICKUP = ["Processing", "Ready for Pickup", "Picked Up", "Cancelled"]
ORDER_STATUS_INSTORE = ["Completed", "Returned"]
STORES = [f"Target - {fake.city() or 'Anytown'}" for _ in range(20)] + ["Target.com"] # Add fallback city
# Ensure stores list isn't empty
if not STORES: STORES = ["Default Store"]
# Ensure sample items have non-empty names/categories and positive price
SAMPLE_ITEMS = [
    (tpl[0] or f"ITEM_UNKNOWN_{i}", tpl[1] or f"Unknown Item {i}", tpl[2] or "General", max(0.01, tpl[3]))
    for i, tpl in enumerate([
        ("ITEM_TV_S", "Samsung 55\" QLED 4K TV", "Televisions", 799.99),
        ("ITEM_LAP_M", "MacBook Air M3", "Computers", 1099.00),
        ("ITEM_PH_A", "Apple iPhone 16", "Mobile Phones", 999.00),
        ("ITEM_HEAD_B", "Bose QuietComfort Ultra", "Headphones", 379.00),
        ("ITEM_COFF", "Keurig K-Mini Coffee Maker", "Home Goods", 79.99),
        ("ITEM_SHIRT", "Goodfellow T-Shirt", "Clothing", 12.00),
        ("ITEM_MILK", "Gallon Whole Milk", "Groceries", 3.50),
        ("ITEM_LEGO", "LEGO Star Wars Set", "Toys", 49.99),
        # Add a default item if the list could somehow be empty
    ])
] or [("ITEM_DEFAULT", "Default Product", "General", 9.99)]
RECOMMENDATION_REASONS = [
    "Frequently purchased together", "Based on your recent browsing history", "Customers who bought items in {category} also bought this",
    "Because you purchased {item_name}", "Popular item in your area", "Based on your interest in {interest}", "Top rated in {category}",
] or ["Recommended for you"] # Fallback reason

# --- Helper Functions (Updated for Non-Empty Placeholders) ---

def _create_random_address() -> Address:
    """Generates an Address object with guaranteed non-empty string fields."""
    street = ""
    # Initialize first, THEN loop
    while not street:
        street = fake.street_address() or "123 Main St" # Fallback

    city = ""
    # Initialize first, THEN loop
    while not city:
        city = fake.city() or "Anytown" # Fallback

    state = ""
    # Initialize first, THEN loop
    while not state:
        state = fake.state_abbr() or "CA" # Fallback

    zip_code = ""
    # Initialize first, THEN loop
    while not zip_code:
        zip_code = fake.zipcode() or "90210" # Fallback

    return Address(street_address=street, city=city, state=state, zip_code=zip_code)

def _create_random_preferences() -> Preferences:
    """Generates Preferences, ensuring lists are non-empty."""
    num_comm = random.randint(1, len(COMMUNICATION_PREFS))
    num_int = random.randint(1, 6)
    comm = random.sample(COMMUNICATION_PREFS, k=num_comm)
    max_interests = len(INTERESTS)
    num_int = max(1, num_int) if max_interests > 0 else 0
    ints = random.sample(INTERESTS, k=min(num_int, max_interests)) if max_interests > 0 else ["general"]
    if not comm: comm = ["email"]
    return Preferences(communication=comm, interests=ints)

def _create_random_item() -> Item:
    """Generates Item, ensuring quantity > 0 and non-empty fields."""
    item_tpl = random.choice(SAMPLE_ITEMS)
    quantity = random.randint(1, 3)
    price = round(item_tpl[3] * random.uniform(0.95, 1.05), 2)
    if price <= 0: price = round(item_tpl[3], 2)
    if price <= 0: price = 0.01
    item_id_base = item_tpl[0]
    item_id_suffix = str(uuid.uuid4())[:4]
    return Item(
        item_id=f"{item_id_base}_{item_id_suffix}" if item_id_base else f"UNKNOWN_{item_id_suffix}",
        item_name=item_tpl[1], # Already ensured non-empty in constant definition
        category=item_tpl[2], # Already ensured non-empty in constant definition
        quantity=quantity,
        price=price
    )

def _create_random_purchase(customer_address: Address) -> Purchase:
    """Generates a Purchase ensuring no fields are None or empty string (uses placeholders)."""
    # Choose constants safely
    chosen_store_name = random.choice(STORES) if STORES else "Default Store"
    chosen_payment_method = random.choice(PAYMENT_METHODS) if PAYMENT_METHODS else "Unknown"
    chosen_order_type = random.choice(ORDER_TYPES) if ORDER_TYPES else "Unknown"

    purchase_obj = Purchase(
        transaction_id="TRANS_" + str(uuid.uuid4()),
        purchase_date="", # Will be overwritten
        delivered_date=PLACEHOLDER_DATE,
        estimated_delivery_date=PLACEHOLDER_DATE,
        store_id=str(random.randint(1000, 9999)),
        store_name=chosen_store_name,
        items=[],
        total_amount=0.01, # Will be overwritten > 0
        payment_method=chosen_payment_method,
        order_type=chosen_order_type,
        shipping_address=customer_address, # Use non-empty customer address
        tracking_number=PLACEHOLDER_TRACKING,
        order_status="" # Will be overwritten
    )

    num_items = random.randint(1, 5)
    purchase_obj.items = [_create_random_item() for _ in range(num_items)]
    purchase_obj.total_amount = round(sum(item.price * item.quantity for item in purchase_obj.items), 2)
    if purchase_obj.items and purchase_obj.total_amount <= 0:
        purchase_obj.total_amount = 0.01

    start_date_2025 = datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    end_date_2025 = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    try:
        purchase_datetime = fake.date_time_between(start_date=start_date_2025, end_date=end_date_2025, tzinfo=datetime.timezone.utc)
    except ValueError as e:
        print(f"Error generating date within 2025: {e}. Falling back.")
        random_day=random.randint(0, 364); random_second=random.randint(0, 86399)
        purchase_datetime = start_date_2025 + datetime.timedelta(days=random_day, seconds=random_second)
    purchase_obj.purchase_date = purchase_datetime.isoformat(timespec='seconds').replace("+00:00", "Z")

    if purchase_obj.order_type == "In-Store":
        status_pool = ORDER_STATUS_INSTORE or ["Unknown"]
        purchase_obj.order_status = random.choice(status_pool)
        if purchase_obj.order_status == "Completed": purchase_obj.delivered_date = purchase_obj.purchase_date
    elif purchase_obj.order_type == "Online - Pickup":
        status_pool = ORDER_STATUS_PICKUP or ["Unknown"]
        purchase_obj.order_status = random.choice(status_pool)
        if purchase_obj.order_status == "Picked Up":
             pickup_delay = datetime.timedelta(days=random.randint(0, 3), hours=random.randint(1, 12))
             delivered_datetime = purchase_datetime + pickup_delay
             if delivered_datetime < purchase_datetime: delivered_datetime = purchase_datetime + datetime.timedelta(minutes=30)
             purchase_obj.delivered_date = delivered_datetime.isoformat(timespec='seconds').replace("+00:00", "Z")
    elif purchase_obj.order_type == "Online - Shipped":
        status_pool = ORDER_STATUS_SHIPPED or ["Unknown"]
        purchase_obj.order_status = random.choice(status_pool)
        # Use a different non-empty address sometimes
        purchase_obj.shipping_address = customer_address if random.random() > 0.15 else _create_random_address()

        if purchase_obj.order_status not in ["Processing", "Cancelled"]:
            est_delivery_delay = datetime.timedelta(days=random.randint(3, 10))
            est_delivery_datetime = purchase_datetime + est_delivery_delay
            purchase_obj.estimated_delivery_date = est_delivery_datetime.isoformat(timespec='seconds').replace("+00:00", "Z")
            tracking = "1Z" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=16))
            purchase_obj.tracking_number = tracking if tracking.strip() else "TRACKING_FAILED" # Ensure non-empty tracking

            if purchase_obj.order_status == "Delivered":
                delivery_delay_min_td = datetime.timedelta(days=1)
                delivery_datetime_min = purchase_datetime + delivery_delay_min_td
                est_dt_obj = est_delivery_datetime
                delivery_datetime_max = est_dt_obj + datetime.timedelta(days=3)
                if delivery_datetime_max < delivery_datetime_min: delivery_datetime_max = delivery_datetime_min + datetime.timedelta(days=1)
                try:
                    delivered_datetime_ts = random.uniform(delivery_datetime_min.timestamp(), delivery_datetime_max.timestamp())
                    delivered_datetime = datetime.datetime.fromtimestamp(delivered_datetime_ts, tz=datetime.timezone.utc)
                except ValueError: delivered_datetime = delivery_datetime_min + datetime.timedelta(hours=random.randint(1, 48))
                if delivered_datetime <= purchase_datetime: delivered_datetime = purchase_datetime + datetime.timedelta(hours=random.randint(1, 24))
                purchase_obj.delivered_date = delivered_datetime.isoformat(timespec='seconds').replace("+00:00", "Z")

    if not purchase_obj.order_status: purchase_obj.order_status = "Unknown" # Final safety check
    return purchase_obj

def _create_random_recommendation(customer_interests: List[str], recent_purchases: List[Purchase]) -> Recommendation:
    """Generates Recommendation ensuring non-empty fields."""
    rec_item_tpl = random.choice(SAMPLE_ITEMS)
    reason_template = random.choice(RECOMMENDATION_REASONS)
    reason = reason_template
    try:
        valid_purchases = [p for p in recent_purchases if p.items]
        if "{category}" in reason_template:
            category_pool = list(set(customer_interests + [item.category for p in valid_purchases for item in p.items]))
            chosen_cat = random.choice(category_pool) if category_pool else "related items"
            reason = reason_template.format(category=chosen_cat)
        elif "{item_name}" in reason_template and valid_purchases:
             most_recent_valid_purchase = valid_purchases[0]
             item_name = random.choice(most_recent_valid_purchase.items).item_name or "a recent item"
             reason = reason_template.format(item_name=item_name)
        elif "{interest}" in reason_template and customer_interests:
             chosen_interest = random.choice(customer_interests) or "your profile"
             reason = reason_template.format(interest=chosen_interest)
    except Exception: pass
    reason = reason.replace("{category}", "related items").replace("{item_name}", "items you viewed").replace("{interest}", "your interests")
    if not reason: reason = "Recommended based on your profile"
    item_id_base = rec_item_tpl[0]
    item_id_suffix = str(uuid.uuid4())[:4]
    return Recommendation(
        item_id=f"{item_id_base}_{item_id_suffix}" if item_id_base else f"REC_UNKNOWN_{item_id_suffix}",
        item_name=rec_item_tpl[1], # Already ensured non-empty
        category=rec_item_tpl[2], # Already ensured non-empty
        reason=reason
    )

def _create_random_customer() -> Customer:
    """Generates a Customer ensuring no fields are None or empty string (uses placeholders)."""
    first_name = fake.first_name() or "First"
    last_name = fake.last_name() or "Last"
    email_user_part = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,99)}"
    email_domain = fake.free_email_domain() or "example.com"
    email = f"{email_user_part}@{email_domain}"

    phone = ""
    # Initialize first, THEN loop
    while not phone:
        raw_phone = fake.phone_number()
        phone = raw_phone.split('x')[0].strip()
        if not phone:
             phone="000-000-0000" # Add fallback if empty after split

    address = _create_random_address() # Guarantees non-empty
    preferences = _create_random_preferences() # Guarantees non-empty

    is_member = random.choice([True, False])
    circle_number = ("TC" + "".join(random.choices("0123456789", k=10))) if is_member else PLACEHOLDER_CIRCLE_NUM

    return Customer(
        customer_id=str(uuid.uuid4()), first_name=first_name, last_name=last_name,
        phone_number=phone, email=email, target_circle_member=is_member,
        target_circle_number=circle_number, address=address, preferences=preferences
    )

# --- Main Function ---
def generate_customer_data(num_customers: int, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Generates a list of random customer profiles with purchase dates exclusively
    within the year 2025. Ensures NO fields in the output have 'null'/'None' values
    OR empty strings (""). Uses descriptive placeholders (like 'DATE_NOT_APPLICABLE')
    for fields where data might not be logically applicable.
    Guarantees valid phone numbers and non-empty address fields.
    """
    if seed is not None:
        Faker.seed(seed); random.seed(seed)
        print(f"--- Using random seed: {seed} ---")
    customer_profiles = []
    print(f"--- Generating {num_customers} random customer profiles (non-null, non-empty) ---")
    for i in range(num_customers):
        customer = _create_random_customer()
        num_purchases = random.randint(1, 8)
        num_recommendations = random.randint(1, 5)
        purchases = [_create_random_purchase(customer.address) for _ in range(num_purchases)]
        purchases.sort(key=lambda p: p.purchase_date, reverse=True)
        recommendations = [_create_random_recommendation(customer.preferences.interests, purchases) for _ in range(num_recommendations)]
        profile_dict = {"customer": asdict(customer), "recent_purchases": [asdict(p) for p in purchases], "recommendations": [asdict(r) for r in recommendations]}
        customer_profiles.append(profile_dict)
        if (i + 1) % 50 == 0 and num_customers >= 50: print(f"  Generated {i+1}/{num_customers} profiles...")
        elif num_customers < 50 and (i+1) % 10 == 0: print(f"  Generated {i+1}/{num_customers} profiles...")
    print(f"--- Generation complete. Returning {len(customer_profiles)} non-null, non-empty profiles. ---")
    customer = _create_random_customer()
    customer.first_name = "Tina"
    customer.last_name = "Bruce"
    customer.email = "tina.bruce111@example.com"
    num_purchases = random.randint(1, 8)
    num_recommendations = random.randint(1, 5)
    purchases = [_create_random_purchase(customer.address) for _ in range(num_purchases)]
    purchases.sort(key=lambda p: p.purchase_date or '0000-01-01T00:00:00Z', reverse=True)
    recommendations = [_create_random_recommendation(customer.preferences.interests, purchases) for _ in range(num_recommendations)]

    profile_dict = {
        "customer": asdict(customer),
        "recent_purchases": [asdict(p) for p in purchases],
        "recommendations": [asdict(r) for r in recommendations]
    }
    customer_profiles.append(profile_dict)
    return customer_profiles
