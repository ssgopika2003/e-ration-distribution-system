import os
import django
from decimal import Decimal
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecom.settings')
django.setup()

from ecomapp.models import OrderItem, Profile
from ecomapp.views import _parse_unit_litres

candidates = []
for oi in OrderItem.objects.select_related('product','order','order__user'):
    prod = oi.product
    if not prod:
        continue
    pn = (prod.prd_name or '').lower()
    cn = (prod.category.catgory_name or '').lower() if prod.category else ''
    db_price = None
    try:
        db_price = Decimal(str(prod.prd_price))
    except Exception:
        db_price = None
    # compute expected display unit price
    is_flour = ('flour' in pn or 'flour' in cn)
    is_rice = any(k in pn or k in cn for k in ('matta','white','raw','rice'))
    unit_l = (_parse_unit_litres(prod.prd_name) or _parse_unit_litres(prod.category.catgory_name) or _parse_unit_litres(prod.prd_des))
    expected_price = db_price
    if is_flour or is_rice:
        expected_price = db_price
    elif 'oil' in pn or 'oil' in cn:
        # find buyer's card type
        user = oi.order.user
        try:
            profile = Profile.objects.get(user=user)
            card_code = (profile.card_type.code or '').upper() if profile and profile.card_type else None
        except Exception:
            card_code = None
        if card_code == 'BPL':
            expected_price = (db_price * Decimal('0.5')).quantize(Decimal('0.01'))
        else:
            if unit_l:
                try:
                    expected_price = (db_price * unit_l).quantize(Decimal('0.01'))
                except Exception:
                    expected_price = db_price
            else:
                expected_price = db_price
    # compare
    if expected_price is not None and Decimal(str(oi.price)) != expected_price:
        candidates.append({
            'order_id': oi.order.id,
            'order_number': oi.order.order_number,
            'user': oi.order.user.username,
            'product': prod.prd_name,
            'stored_price': Decimal(str(oi.price)),
            'db_price': db_price,
            'expected_price': expected_price,
            'quantity': oi.quantity,
        })

print(f"Found {len(candidates)} OrderItems that would change:")
for c in candidates:
    print(c)
