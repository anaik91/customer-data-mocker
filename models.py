import datetime
import json
import random
import uuid # For unique IDs
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from faker import Faker

# --- Class Definitions (Same as before) ---
@dataclass
class Address:
    street_address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, str]]) -> Optional['Address']:
        if data is None: return None
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class Preferences:
    communication: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, List[str]]]) -> 'Preferences':
        if data is None: return cls()
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class Item:
    item_id: str = ""
    item_name: str = ""
    category: str = ""
    quantity: int = 0
    price: float = 0.0

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Item']:
        if data is None: return None
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class Purchase:
    transaction_id: str = ""
    purchase_date: Optional[str] = None
    delivered_date: Optional[str] = None
    estimated_delivery_date: Optional[str] = None
    store_id: str = ""
    store_name: str = ""
    items: List[Item] = field(default_factory=list)
    total_amount: float = 0.0
    payment_method: str = ""
    order_type: str = ""
    shipping_address: Optional[Address] = None
    tracking_number: Optional[str] = None
    order_status: str = ""

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Purchase']:
        if data is None: return None
        items_data = data.get("items", [])
        shipping_address_data = data.get("shipping_address")
        valid_data = {k: v for k, v in data.items() if k in cls.__annotations__}
        valid_data["items"] = [Item.from_dict(item_data) for item_data in items_data if item_data]
        valid_data["shipping_address"] = Address.from_dict(shipping_address_data)
        return cls(**valid_data)

@dataclass
class Recommendation:
    item_id: str = ""
    item_name: str = ""
    category: str = ""
    reason: str = ""

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Recommendation']:
        if data is None: return None
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class Customer:
    customer_id: str = ""
    first_name: str = ""
    last_name: str = ""
    phone_number: str = "" # Will ensure this is non-empty and no extension
    email: str = ""
    target_circle_member: bool = False
    target_circle_number: Optional[str] = None
    address: Address = field(default_factory=Address)
    preferences: Preferences = field(default_factory=Preferences)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Customer']:
        if data is None: return None
        address_data = data.get("address")
        preferences_data = data.get("preferences")
        valid_data = {k: v for k, v in data.items() if k in cls.__annotations__}
        valid_data["address"] = Address.from_dict(address_data) if address_data else Address()
        valid_data["preferences"] = Preferences.from_dict(preferences_data) if preferences_data else Preferences()
        return cls(**valid_data)


# --- Data Generation Setup ---
fake = Faker()

# --- Constants (Same as before) ---
COMMUNICATION_PREFS = ["email", "text", "phone", "mail"]
INTERESTS = ["electronics", "home goods", "clothing", "groceries", "toys", "books", "sports", "outdoors", "beauty", "pharmacy", "baby", "pets", "entertainment"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "Cash", "Target Credit Card", "Gift Card", "PayPal"]
ORDER_TYPES = ["In-Store", "Online - Shipped", "Online - Pickup"]
ORDER_STATUS_SHIPPED = ["Processing", "Shipped", "In Transit", "Out for Delivery", "Delivered", "Delayed", "Cancelled"]
ORDER_STATUS_PICKUP = ["Processing", "Ready for Pickup", "Picked Up", "Cancelled"]
ORDER_STATUS_INSTORE = ["Completed", "Returned"]
STORES = [f"Target - {fake.city()}" for _ in range(20)] + ["Target.com"]
SAMPLE_ITEMS = [
    ("ITEM_TV_S", "Samsung 55\" QLED 4K TV", "Televisions", 799.99), ("ITEM_LAP_M", "MacBook Air M3", "Computers", 1099.00),
    ("ITEM_PH_A", "Apple iPhone 16", "Mobile Phones", 999.00), ("ITEM_HEAD_B", "Bose QuietComfort Ultra", "Headphones", 379.00),
    ("ITEM_COFF", "Keurig K-Mini Coffee Maker", "Home Goods", 79.99), ("ITEM_SHIRT", "Goodfellow T-Shirt", "Clothing", 12.00),
    ("ITEM_MILK", "Gallon Whole Milk", "Groceries", 3.50), ("ITEM_LEGO", "LEGO Star Wars Set", "Toys", 49.99),
]
RECOMMENDATION_REASONS = [
    "Frequently purchased together", "Based on your recent browsing history", "Customers who bought items in {category} also bought this",
    "Because you purchased {item_name}", "Popular item in your area", "Based on your interest in {interest}", "Top rated in {category}",
]


# --- Helper Functions for Random Data Generation ---

def _create_random_address() -> Address:
    """Generates an Address object with non-empty fields."""
    street = ""
    while not street: street = fake.street_address()
    city = ""
    while not city: city = fake.city()
    state = ""
    while not state: state = fake.state_abbr()
    zip_code = ""
    while not zip_code: zip_code = fake.zipcode()
    return Address(street_address=street, city=city, state=state, zip_code=zip_code)

def _create_random_preferences() -> Preferences:
    # (Same as before)
    num_comm = random.randint(1, len(COMMUNICATION_PREFS))
    num_int = random.randint(1, 6)
    return Preferences(
        communication=random.sample(COMMUNICATION_PREFS, k=num_comm),
        interests=random.sample(INTERESTS, k=min(num_int, len(INTERESTS)))
    )

def _create_random_item() -> Item:
    # (Same as before)
    item_tpl = random.choice(SAMPLE_ITEMS)
    return Item(
        item_id=item_tpl[0] + "_" + str(uuid.uuid4())[:4], item_name=item_tpl[1], category=item_tpl[2],
        quantity=random.randint(1, 3), price=round(item_tpl[3] * random.uniform(0.9, 1.1), 2)
    )

def _create_random_purchase(customer_address: Address) -> Purchase:
    # (Same logic as before)
    # ... (purchase generation logic) ...
    purchase_obj = Purchase(transaction_id="TRANS_" + str(uuid.uuid4()))
    purchase_obj.store_id = str(random.randint(1000, 9999))
    purchase_obj.store_name = random.choice(STORES)
    purchase_obj.payment_method = random.choice(PAYMENT_METHODS)
    purchase_obj.order_type = random.choice(ORDER_TYPES)
    num_items = random.randint(1, 5)
    purchase_obj.items = [_create_random_item() for _ in range(num_items)]
    purchase_obj.total_amount = round(sum(item.price * item.quantity for item in purchase_obj.items), 2)
    purchase_datetime = fake.date_time_between(start_date="-2y", end_date="now", tzinfo=datetime.timezone.utc)
    purchase_obj.purchase_date = purchase_datetime.isoformat(timespec='seconds').replace("+00:00", "Z")

    if purchase_obj.order_type == "In-Store":
        purchase_obj.order_status = random.choice(ORDER_STATUS_INSTORE)
        purchase_obj.delivered_date = purchase_obj.purchase_date if purchase_obj.order_status == "Completed" else None
        purchase_obj.shipping_address = None
    elif purchase_obj.order_type == "Online - Pickup":
        purchase_obj.order_status = random.choice(ORDER_STATUS_PICKUP)
        purchase_obj.shipping_address = None
        if purchase_obj.order_status == "Picked Up":
             pickup_delay = datetime.timedelta(days=random.randint(0, 3), hours=random.randint(1, 12))
             delivered_datetime = min(purchase_datetime + pickup_delay, datetime.datetime.now(datetime.timezone.utc))
             if delivered_datetime < purchase_datetime:
                 delivered_datetime = purchase_datetime + datetime.timedelta(hours=1); delivered_datetime = min(delivered_datetime, datetime.datetime.now(datetime.timezone.utc))
             purchase_obj.delivered_date = delivered_datetime.isoformat(timespec='seconds').replace("+00:00", "Z")
    elif purchase_obj.order_type == "Online - Shipped":
        purchase_obj.order_status = random.choice(ORDER_STATUS_SHIPPED)
        purchase_obj.shipping_address = customer_address if random.random() > 0.15 else _create_random_address()
        if purchase_obj.order_status not in ["Processing", "Cancelled"]:
            est_delivery_delay = datetime.timedelta(days=random.randint(3, 10))
            est_delivery_datetime = purchase_datetime + est_delivery_delay
            purchase_obj.estimated_delivery_date = est_delivery_datetime.isoformat(timespec='seconds').replace("+00:00", "Z")
            purchase_obj.tracking_number = "1Z" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=16))
            if purchase_obj.order_status == "Delivered":
                delivery_delay_min = datetime.timedelta(days=1)
                delivery_datetime_min = purchase_datetime + delivery_delay_min
                delivery_datetime_max = est_delivery_datetime + datetime.timedelta(days=3)
                if delivery_datetime_max < delivery_datetime_min: delivery_datetime_max = delivery_datetime_min + datetime.timedelta(days=1)
                try:
                    delivered_datetime_ts = random.uniform(delivery_datetime_min.timestamp(), delivery_datetime_max.timestamp())
                    delivered_datetime = datetime.datetime.fromtimestamp(delivered_datetime_ts, tz=datetime.timezone.utc)
                except ValueError: delivered_datetime = delivery_datetime_min + datetime.timedelta(hours=random.randint(1, 24))
                delivered_datetime = min(delivered_datetime, datetime.datetime.now(datetime.timezone.utc))
                if delivered_datetime < purchase_datetime: delivered_datetime = purchase_datetime + datetime.timedelta(hours=random.randint(1, 24)); delivered_datetime = min(delivered_datetime, datetime.datetime.now(datetime.timezone.utc))
                purchase_obj.delivered_date = delivered_datetime.isoformat(timespec='seconds').replace("+00:00", "Z")
    return purchase_obj


def _create_random_recommendation(customer_interests: List[str], recent_purchases: List[Purchase]) -> Recommendation:
    # (Same logic as before)
    # ... (recommendation generation logic) ...
    rec_item_tpl = random.choice(SAMPLE_ITEMS)
    reason_template = random.choice(RECOMMENDATION_REASONS)
    reason = reason_template
    try:
        valid_purchases = [p for p in recent_purchases if p.items]
        if "{category}" in reason_template:
            category_pool = list(set(customer_interests + [item.category for p in valid_purchases for item in p.items]))
            if category_pool: reason = reason_template.format(category=random.choice(category_pool))
            else: reason = reason_template.format(category="related items")
        elif "{item_name}" in reason_template and valid_purchases:
             most_recent_valid_purchase = valid_purchases[0]
             reason = reason_template.format(item_name=random.choice(most_recent_valid_purchase.items).item_name)
        elif "{interest}" in reason_template and customer_interests:
             reason = reason_template.format(interest=random.choice(customer_interests))
    except Exception: pass
    reason = reason.replace("{category}", "related items").replace("{item_name}", "items you viewed").replace("{interest}", "your interests")
    return Recommendation(
        item_id=rec_item_tpl[0] + "_" + str(uuid.uuid4())[:4], item_name=rec_item_tpl[1],
        category=rec_item_tpl[2], reason=reason
    )

# --- MODIFIED HELPER FUNCTION ---
def _create_random_customer() -> Customer:
    """Generates a Customer object ensuring non-empty phone number (no extension) and address."""
    first_name = fake.first_name()
    last_name = fake.last_name()
    email_user = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,99)}"

    # Ensure phone number is generated, non-empty, and without extension
    phone = ""
    while not phone:
        raw_phone = fake.phone_number()
        # Split at the extension 'x' and take the first part (the main number)
        phone = raw_phone.split('x')[0].strip() # Use strip() just in case
        # Ensure the result after splitting isn't empty (highly unlikely but safe)
        if not phone:
            continue # Retry generation if splitting resulted in empty string

    # Generate address using the updated helper that ensures non-empty fields
    address = _create_random_address()

    cust = Customer(
        customer_id=str(uuid.uuid4()),
        first_name=first_name,
        last_name=last_name,
        phone_number=phone, # Assign the processed, non-empty phone number
        email=f"{email_user}@{fake.free_email_domain()}",
        target_circle_member=random.choice([True, False]),
        address=address,
        preferences=_create_random_preferences()
    )
    cust.target_circle_number = "TC" + "".join(random.choices("0123456789", k=10)) if cust.target_circle_member else None
    return cust


# --- Main Function to Generate Data (No changes needed here) ---
def generate_customer_data(num_customers: int, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Generates a list of random customer profiles ensuring valid phone numbers
    (non-null, non-empty, no extension) and addresses (non-null, non-empty).
    """
    if seed is not None:
        Faker.seed(seed)
        random.seed(seed)
        print(f"--- Using random seed: {seed} ---")

    customer_profiles = []

    print(f"--- Generating {num_customers} random customer profiles ---")
    for i in range(num_customers):
        customer = _create_random_customer()
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

        # Progress indicator
        if (i + 1) % 50 == 0 and num_customers >= 50:
             print(f"  Generated {i+1}/{num_customers} profiles...")
        elif num_customers < 50 and (i+1) % 10 == 0:
             print(f"  Generated {i+1}/{num_customers} profiles...")

    print(f"--- Generation complete. Returning {len(customer_profiles)} profiles. ---")
    return customer_profiles