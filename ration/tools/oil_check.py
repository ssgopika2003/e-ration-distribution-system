import os
import django
from decimal import Decimal
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ecom.settings')
django.setup()
from ecomapp.models import Cart, Profile
from ecomapp.views import _compute_cart_oil_litres_for_user, _parse_unit_litres, get_limits_for_profile, get_family_size

users = set(it.user for it in Cart.objects.select_related('user').all())
print('Oil limits per user:')
for u in users:
    try:
        profile = Profile.objects.get(user=u)
    except Profile.DoesNotExist:
        profile = None
    limits = get_limits_for_profile(profile)
    members = get_family_size(profile)
    card_code = (profile.card_type.code or '').upper() if profile and profile.card_type else None
    oil_limit_value = limits.get('oil')
    try:
        oil_limit_value = Decimal(str(oil_limit_value)) if oil_limit_value is not None else None
    except Exception:
        oil_limit_value = None
    if oil_limit_value is None:
        allowed_oil_l = None
    else:
        allowed_oil_l = oil_limit_value if card_code == 'BPL' else (oil_limit_value * Decimal(members))
    cart_oil_l = _compute_cart_oil_litres_for_user(u)
    print(f"User={u.username} card={card_code} members={members} allowed_oil_l={allowed_oil_l} cart_oil_l={cart_oil_l}")
