from decimal import Decimal
from django.db import transaction
from ecomapp.models import OrderItem, Order, Profile
from ecomapp.views import _parse_unit_litres

changed_orders = set()
summary = []
with transaction.atomic():
    for oi in OrderItem.objects.select_related('product','order','order__user'):
        prod = oi.product
        if not prod:
            continue
        pn = (prod.prd_name or '').lower()
        cn = (prod.category.catgory_name or '').lower() if prod.category else ''
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
        # compare and update
        if expected_price is not None and Decimal(str(oi.price)) != expected_price:
            old_price = Decimal(str(oi.price))
            oi.price = expected_price
            oi.save(update_fields=['price'])
            changed_orders.add(oi.order.id)
            summary.append((oi.order.id, oi.order.order_number, oi.order.user.username, prod.prd_name, old_price, expected_price, oi.quantity))

    # Recompute totals for affected orders
    for oid in changed_orders:
        order = Order.objects.get(id=oid)
        total = Decimal('0.00')
        for it in order.items.all():
            total += (it.price * it.quantity)
        order.total_amount = total.quantize(Decimal('0.01'))
        order.save(update_fields=['total_amount'])

print('Backfill complete. Summary:')
for row in summary:
    print(row)
print('Updated orders:', list(changed_orders))
