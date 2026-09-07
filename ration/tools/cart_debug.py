import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecom.settings')
django.setup()

from ecomapp.models import Cart, Profile
from ecomapp.views import _parse_unit_litres

print('Cart debug dump:')
for it in Cart.objects.all().select_related('product','product__category','user'):
    pn = (it.product.prd_name or '').lower()
    cn = (it.product.category.catgory_name or '').lower() if it.product.category else ''
    try:
        db_unit_price = Decimal(str(it.product.prd_price))
    except Exception:
        db_unit_price = Decimal('0')
    unit_l = (_parse_unit_litres(it.product.prd_name) or _parse_unit_litres(it.product.category.catgory_name) or _parse_unit_litres(it.product.prd_des))
    is_flour = ('flour' in pn or 'flour' in cn)
    is_oil = ('oil' in pn or 'oil' in cn)
    is_rice = any(k in pn or k in cn for k in ('matta','white','raw','rice'))
    # determine user's card code if available
    card_code = None
    try:
        profile = Profile.objects.get(user=it.user)
        card_code = (profile.card_type.code or '').upper() if profile and profile.card_type else None
    except Exception:
        card_code = None
    # compute display price using same logic as views
    display_unit_price = db_unit_price
    display_unit_label = None
    if is_flour:
        display_unit_price = db_unit_price
        display_unit_label = '1 kg'
    elif is_oil:
        if card_code == 'BPL':
            display_unit_price = (db_unit_price * Decimal('0.5')).quantize(Decimal('0.01'))
            display_unit_label = '500 ml'
        else:
            if unit_l:
                try:
                    display_unit_price = (db_unit_price * unit_l).quantize(Decimal('0.01'))
                except Exception:
                    display_unit_price = db_unit_price
                if unit_l < Decimal('1'):
                    ml = (unit_l * Decimal('1000')).quantize(Decimal('1'))
                    display_unit_label = f"{ml} ml"
                else:
                    display_unit_label = f"{unit_l.normalize()} L"
            else:
                display_unit_price = db_unit_price
                display_unit_label = None
    elif is_rice:
        display_unit_price = db_unit_price
        display_unit_label = '1 kg'
    # compute totals
    try:
        display_total = (display_unit_price * Decimal(str(it.quantity))).quantize(Decimal('0.01'))
    except Exception:
        display_total = (display_unit_price * Decimal(it.quantity))
    print(f"User={getattr(it.user,'username',None)} Prod={it.product.prd_name!r} qty={it.quantity} db_price={db_unit_price} unit_l={unit_l} card_code={card_code} is_flour={is_flour} is_oil={is_oil} display_unit_price={display_unit_price} display_total={display_total}")
