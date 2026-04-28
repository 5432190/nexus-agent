# Patch commerce.py to auto-confirm with Stripe's test card
from pathlib import Path

p = Path("nexus_agent/tools/commerce.py")
content = p.read_text(encoding="utf-8")

# Find the PaymentIntent.create call and inject test card params
old_call = "payment = stripe.PaymentIntent.create("
new_call = """payment = stripe.PaymentIntent.create(
            payment_method="pm_card_visa",
            confirm=True,"""

if old_call in content and "pm_card_visa" not in content:
    content = content.replace(old_call, new_call)
    p.write_text(content, encoding="utf-8")
    print("✅ Added test card + auto-confirm to commerce.py")
else:
    print("ℹ️  Already patched or pattern not found")
