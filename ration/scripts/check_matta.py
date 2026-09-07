from django.contrib.auth.models import User
from ecomapp.models import Profile, Cart

username = 'sinthu'
user = User.objects.filter(username__iexact=username).first()
if not user:
    user = User.objects.first()
    print('User "sinthu" not found — using first user:', user.username)
else:
    print('Using user:', user.username)

profile = Profile.objects.filter(user=user).first()
if not profile:
    print('No profile for user')

members = 0
if profile:
    members = profile.family_members or profile.members.count()
members = members or 1
limits = {'matta': 2, 'white': 2, 'raw': 1}
allowed_matta = limits['matta'] * members

cart_total = 0
for it in Cart.objects.filter(user=user):
    pn = (it.product.prd_name or '').lower()
    cn = (it.product.category.catgory_name or '').lower() if it.product.category else ''
    if 'matta' in pn or 'matta' in cn:
        cart_total += it.quantity

print(f'members={members}, allowed_matta={allowed_matta}, cart_matta_total={cart_total}')
