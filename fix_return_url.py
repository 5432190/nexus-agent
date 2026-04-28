from pathlib import Path

p = Path("nexus_agent/tools/commerce.py")
content = p.read_text(encoding="utf-8")

# Add return_url to PaymentIntent.create call
old = 'payment = stripe.PaymentIntent.create('
new = '''payment = stripe.PaymentIntent.create(
            return_url="https://example.com/return",'''

if old in content and "return_url" not in content:
    content = content.replace(old, new)
    p.write_text(content, encoding="utf-8")
    print("✅ Added return_url to Stripe call")
else:
    print("ℹ️ Already patched or pattern not found")
