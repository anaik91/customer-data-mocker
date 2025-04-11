import datetime
import json
import random
import uuid # For unique IDs
from dataclasses import dataclass, field, asdict # Import asdict for simpler to_dict
from typing import List, Optional, Dict, Any
from faker import Faker # Import Faker

# --- Class Definitions (Best practice: Keep these outside the generation function) ---

@dataclass
class Address:
    street_address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""

    # Using asdict is often simpler for nested dataclasses if the structure matches JSON
    # def to_dict(self) -> Dict[str, str]:
    #     return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, str]]) -> Optional['Address']:
        if data is None: return None
        # Allow creation even if some keys are missing in source dict
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Preferences:
    communication: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)

    # def to_dict(self) -> Dict[str, List[str]]:
    #     return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> 'Preferences':
         # Allow creation even if some keys are missing in source dict
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Item:
    item_id: str = ""
    item_name: str = ""
    category: str = ""
    quantity: int = 0
    price: float = 0.0

    # def to_dict(self) -> Dict[str, Any]:
    #     return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
         # Allow creation even if some keys are missing in source dict
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

    # Manual to_dict needed if nested classes don't use asdict or need custom logic
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["items"] = [item_data for item_data in data.get("items", [])] # Already dicts from asdict
        data["shipping_address"] = data.get("shipping_address") # Already dict from asdict
        return data


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Purchase':
        items_data = data.get("items", [])
        shipping_address_data = data.get("shipping_address")

        # Filter data to only include keys present in the class definition
        valid_data = {k: v for k, v in data.items() if k in cls.__annotations__}

        # Re-instantiate nested objects
        valid_data["items"] = [Item.from_dict(item_data) for item_data in items_data] if items_data else []
        valid_data["shipping_address"] = Address.from_dict(shipping_address_data) if shipping_address_data else None

        return cls(**valid_data)


@dataclass
class Recommendation:
    item_id: str = ""
    item_name: str = ""
    category: str = ""
    reason: str = ""

    # def to_dict(self) -> Dict[str, str]:
    #     return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recommendation':
         # Allow creation even if some keys are missing in source dict
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Customer:
    customer_id: str = ""
    first_name: str = ""
    last_name: str = ""
    phone_number: str = ""
    email: str = ""
    target_circle_member: bool = False
    target_circle_number: Optional[str] = None # Make Optional
    address: Address = field(default_factory=Address)
    preferences: Preferences = field(default_factory=Preferences)

    # Manual to_dict needed if nested classes don't use asdict or need custom logic
    def to_dict(self) -> Dict[str, Any]:
       data = asdict(self) # Convert base Customer attributes
       # asdict handles nested dataclasses correctly by default
       # data["address"] = self.address.to_dict() # Only needed if Address doesn't use asdict or has custom logic
       # data["preferences"] = self.preferences.to_dict() # Only needed if Preferences doesn't use asdict or has custom logic
       return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Customer':
        address_data = data.get("address", {})
        preferences_data = data.get("preferences", {})

        # Filter data to only include keys present in the class definition
        valid_data = {k: v for k, v in data.items() if k in cls.__annotations__}

        # Re-instantiate nested objects
        valid_data["address"] = Address.from_dict(address_data) if address_data else Address() # Provide default if missing
        valid_data["preferences"] = Preferences.from_dict(preferences_data) if preferences_data else Preferences() # Provide default if missing

        return cls(**valid_data)


# --- Data Generation Setup (Constants & Faker instance can be global) ---
fake = Faker()

# Constants for random choices
COMMUNICATION_PREFS = ["email", "text", "phone", "mail"]
INTERESTS = ["electronics", "home goods", "clothing", "groceries", "toys", "books", "sports", "outdoors", "beauty", "pharmacy", "baby", "pets", "entertainment"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "Cash", "Target Credit Card", "Gift Card", "PayPal"]
ORDER_TYPES = ["In-Store", "Online - Shipped", "Online - Pickup"]
ORDER_STATUS_SHIPPED = ["Processing", "Shipped", "In Transit", "Out for Delivery", "Delivered", "Delayed", "Cancelled"]
ORDER_STATUS_PICKUP = ["Processing", "Ready for Pickup", "Picked Up", "Cancelled"]
ORDER_STATUS_INSTORE = ["Completed", "Returned"] # Simplified
STORES = [f"Target - {fake.city()}" for _ in range(20)] + ["Target.com"] # Sample stores
SAMPLE_ITEMS = [
    ("ITEM_TV_S", "Samsung 55\" QLED 4K TV", "Televisions", 799.99), ("ITEM_TV_L", "LG 65\" OLED 4K TV", "Televisions", 1499.99),
    ("ITEM_LAP_M", "MacBook Air M3", "Computers", 1099.00), ("ITEM_LAP_D", "Dell XPS 15 Laptop", "Computers", 1399.00),
    ("ITEM_PH_A", "Apple iPhone 16", "Mobile Phones", 999.00), ("ITEM_PH_S", "Samsung Galaxy S25", "Mobile Phones", 899.00),
    ("ITEM_HEAD_B", "Bose QuietComfort Ultra", "Headphones", 379.00), ("ITEM_HEAD_S", "Sony WH-1000XM5", "Headphones", 349.00),
    ("ITEM_SPK_S", "Sonos Era 100", "Speakers", 249.00), ("ITEM_COFF", "Keurig K-Mini Coffee Maker", "Home Goods", 79.99),
    ("ITEM_VAC_D", "Dyson V11 Cordless Vacuum", "Home Goods", 599.99), ("ITEM_SHIRT", "Goodfellow T-Shirt", "Clothing", 12.00),
    ("ITEM_JEANS", "Levi's 501 Jeans", "Clothing", 59.50), ("ITEM_MILK", "Gallon Whole Milk", "Groceries", 3.50),
    ("ITEM_BREAD", "Wonder Bread", "Groceries", 2.80), ("ITEM_LEGO", "LEGO Star Wars Set", "Toys", 49.99),
    ("ITEM_BOOK_H", "The latest bestseller", "Books", 22.00), ("ITEM_BBALL", "Spalding Basketball", "Sports", 29.99),
    ("ITEM_LIP", "Revlon Lipstick", "Beauty", 8.99), ("ITEM_TYL", "Tylenol Extra Strength", "Pharmacy", 9.99),
    ("ITEM_DIAP", "Pampers Diapers", "Baby", 26.99), ("ITEM_DOGF", "Purina Pro Plan Dog Food", "Pets", 45.00),
]
RECOMMENDATION_REASONS = [
    "Frequently purchased together", "Based on your recent browsing history", "Customers who bought items in {category} also bought this",
    "Because you purchased {item_name}", "Popular item in your area", "Based on your interest in {interest}", "Top rated in {category}",
]

# --- Helper Functions for Random Data Generation (Keep outside main function) ---

def _create_random_address() -> Address:
    return Address(street_address=fake.street_address(), city=fake.city(), state=fake.state_abbr(), zip_code=fake.zipcode())

def _create_random_preferences() -> Preferences:
    num_comm = random.randint(1, len(COMMUNICATION_PREFS))
    num_int = random.randint(1, 6)
    return Preferences(
        communication=random.sample(COMMUNICATION_PREFS, k=num_comm),
        interests=random.sample(INTERESTS, k=min(num_int, len(INTERESTS)))
    )

def _create_random_item() -> Item:
    item_tpl = random.choice(SAMPLE_ITEMS)
    return Item(
        item_id=item_tpl[0] + "_" + str(uuid.uuid4())[:4], item_name=item_tpl[1], category=item_tpl[2],
        quantity=random.randint(1, 3), price=round(item_tpl[3] * random.uniform(0.9, 1.1), 2)
    )

def _create_random_purchase(customer_address: Address) -> Purchase:
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
             purchase_obj.delivered_date = delivered_datetime.isoformat(timespec='seconds').replace("+00:00", "Z")
    elif purchase_obj.order_type == "Online - Shipped":
        purchase_obj.order_status = random.choice(ORDER_STATUS_SHIPPED)
        purchase_obj.shipping_address = customer_address if random.random() > 0.2 else _create_random_address()

        if purchase_obj.order_status not in ["Processing", "Cancelled"]:
            est_delivery_delay = datetime.timedelta(days=random.randint(3, 10))
            est_delivery_datetime = purchase_datetime + est_delivery_delay
            purchase_obj.estimated_delivery_date = est_delivery_datetime.isoformat(timespec='seconds').replace("+00:00", "Z")
            purchase_obj.tracking_number = "1Z" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=16))

            if purchase_obj.order_status == "Delivered":
                delivery_delay_min = datetime.timedelta(days=1)
                delivery_datetime_min = max(purchase_datetime + delivery_delay_min, purchase_datetime + datetime.timedelta(hours=1)) # At least 1hr after purchase
                delivery_datetime_max = est_delivery_datetime + datetime.timedelta(days=2)
                if delivery_datetime_max < delivery_datetime_min: delivery_datetime_max = delivery_datetime_min + datetime.timedelta(days=1)
                delivered_datetime_ts = random.uniform(delivery_datetime_min.timestamp(), delivery_datetime_max.timestamp())
                delivered_datetime = datetime.datetime.fromtimestamp(delivered_datetime_ts, tz=datetime.timezone.utc)
                delivered_datetime = min(delivered_datetime, datetime.datetime.now(datetime.timezone.utc)) # Not in future
                purchase_obj.delivered_date = delivered_datetime.isoformat(timespec='seconds').replace("+00:00", "Z")

    return purchase_obj

def _create_random_recommendation(customer_interests: List[str], recent_purchases: List[Purchase]) -> Recommendation:
    rec_item_tpl = random.choice(SAMPLE_ITEMS)
    reason = random.choice(RECOMMENDATION_REASONS)
    try:
        valid_purchases = [p for p in recent_purchases if p.items]
        if "{category}" in reason:
            category_pool = customer_interests + [item.category for p in valid_purchases for item in p.items]
            reason = reason.format(category=random.choice(category_pool)) if category_pool else reason.format(category="related items")
        elif "{item_name}" in reason and valid_purchases:
             reason = reason.format(item_name=valid_purchases[0].items[0].item_name)
        elif "{interest}" in reason and customer_interests:
             reason = reason.format(interest=random.choice(customer_interests))
    except Exception: pass
    reason = reason.replace("{category}", "related items").replace("{item_name}", "your recent purchase").replace("{interest}", "your interests")
    return Recommendation(
        item_id=rec_item_tpl[0] + "_" + str(uuid.uuid4())[:4], item_name=rec_item_tpl[1],
        category=rec_item_tpl[2], reason=reason
    )

def _create_random_customer() -> Customer:
    first_name = fake.first_name()
    last_name = fake.last_name()
    cust = Customer(
        customer_id=str(uuid.uuid4()), first_name=first_name, last_name=last_name,
        phone_number=fake.phone_number(), email=f"{first_name.lower()}.{last_name.lower()}{random.randint(1,99)}@{fake.free_email_domain()}",
        target_circle_member=random.choice([True, False]), address=_create_random_address(), preferences=_create_random_preferences()
    )
    cust.target_circle_number = "TC" + "".join(random.choices("0123456789", k=10)) if cust.target_circle_member else None
    return cust


# --- Main Function to Generate Data and Return as JSON-Serializable List ---

def generate_customer_data(num_customers: int, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Generates a list of random customer profiles.

    Args:
        num_customers: The number of customer profiles to generate.
        seed: Optional integer seed for reproducibility.

    Returns:
        A list of dictionaries, where each dictionary represents a customer profile
        and is suitable for JSON serialization.
    """
    if seed is not None:
        Faker.seed(seed)
        random.seed(seed)
        print(f"Using random seed: {seed}")

    customer_object_list = [] # Holds dictionaries with objects first

    print(f"Generating {num_customers} random customer data entries...")
    for i in range(num_customers):
        customer = _create_random_customer()
        # Ensure at least 1 purchase/recommendation
        num_purchases = random.randint(1, 10)
        num_recommendations = random.randint(1, 5)

        purchases = [_create_random_purchase(customer.address) for _ in range(num_purchases)]
        purchases.sort(key=lambda p: p.purchase_date or '', reverse=True)

        recommendations = [_create_random_recommendation(customer.preferences.interests, purchases) for _ in range(num_recommendations)]

        # Append the dictionary containing the *objects*
        customer_object_list.append({
            "customer": customer,
            "recent_purchases": purchases,
            "recommendations": recommendations
        })
        if (i + 1) % 10 == 0 and num_customers >= 10:
            print(f"  Generated {i+1}/{num_customers}...")
    print("Generation complete.")

    # Convert the list of object-containing dictionaries to JSON-serializable dictionaries
    print("Converting data to JSON format...")
    customer_data_dict_list = []
    for entry in customer_object_list:
        customer_data_dict_list.append({
             # Use asdict for nested conversion if classes support it well,
             # otherwise use the specific .to_dict() methods
            "customer": asdict(entry["customer"]),
            "recent_purchases": [asdict(p) for p in entry["recent_purchases"]],
            "recommendations": [asdict(r) for r in entry["recommendations"]]
        })
    print("Conversion complete.")

    return customer_data_dict_list