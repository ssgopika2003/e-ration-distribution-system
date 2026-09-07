import os
import django
from decimal import Decimal
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ecom.settings')
django.setup()
from ecomapp.models import Order, Profile
from ecomapp.views import _parse_unit_litres

ORDER_NUMBER = 'ORD34F55829'
try:
    order = Order.objects.get(order_number=ORDER_NUMBER)
except Order.DoesNotExist:
    print('Order not found:', ORDER_NUMBER)
    raise SystemExit(0)

print('Order:', order.id, order.order_number, 'user=', order.user.username, 'payment_method=', order.payment_method, 'total_amount=', order.total_amount)

# profile info
try:
    profile = Profile.objects.get(user=order.user)
    card_code = (profile.card_type.code or '').upper() if profile and profile.card_type else None
except Exception:
    profile = None
    card_code = None
print('Profile card_code:', card_code)

rice_subtotal = Decimal('0.00')
non_discount_total = Decimal('0.00')
print('\nItems:')
for it in order.items.select_related('product'):
    pn = (it.product.prd_name or '').lower() if it.product else ''
    cn = (it.product.category.catgory_name or '').lower() if it.product and it.product.category else ''
    is_rice = any(k in pn or k in cn for k in ('matta','white','raw','rice'))
    line = it.price * it.quantity
    print(' -', it.product.prd_name if it.product else 'N/A', 'qty=', it.quantity, 'stored_price=', it.price, 'line_total=', line, 'is_rice=', is_rice)
    if is_rice:
        rice_subtotal += line
    else:
        non_discount_total += line

print('\nRice subtotal =', rice_subtotal)
# discount pct from profile/card
if card_code == 'APL':
    discount_pct = Decimal('0.9273')
elif card_code == 'BPL':
    discount_pct = Decimal('1.00')
else:
    discount_pct = Decimal('0.00')

discount_amount = (rice_subtotal * discount_pct).quantize(Decimal('0.01'))
rice_after_discount = (rice_subtotal - discount_amount).quantize(Decimal('0.01'))
total_after_discount = (rice_after_discount + non_discount_total).quantize(Decimal('0.01'))
print('discount_pct=', discount_pct, 'discount_amount=', discount_amount)
print('rice_after_discount=', rice_after_discount)
print('non_discount_total=', non_discount_total)
print('total_after_discount (computed)=', total_after_discount)

amount_paid = order.total_amount if order.payment_method in ('upi','netbanking') else Decimal('0.00')
amount_due_on_delivery = order.total_amount if order.payment_method == 'cod' else Decimal('0.00')
print('\namount_paid=', amount_paid, 'amount_due_on_delivery=', amount_due_on_delivery)
