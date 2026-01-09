from src.data_loader import get_macro_indicators, get_asset_info
from src.allocator import get_allocation_strategy

print("--- Testing Macro Data ---")
macro = get_macro_indicators()
print(f"Macro Data: {macro}")

print("\n--- Testing Asset Data (Values) ---")
info = get_asset_info("VALE3.SA")
if info:
    print(f"Fetched VALE3: Price={info.get('price')}, ROE={info.get('roe')}")
else:
    print("Failed to fetch VALE3")

print("\n--- Testing Asset Data (Crypto) ---")
info_c = get_asset_info("BTC-USD")
if info_c:
    print(f"Fetched BTC: Price={info_c.get('price')}")
else:
    print("Failed to fetch BTC")

print("\n--- Testing Allocation ---")
alloc = get_allocation_strategy("Moderado")
print(f"Moderado Allocation: {alloc}")
print("Verification Complete.")
