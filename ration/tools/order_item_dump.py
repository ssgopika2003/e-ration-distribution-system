import django, os
from decimal import Decimal
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecom.settings')
django.setup()
from ecomapp.models import Order, OrderItem

print('Recent orders and item prices:')
for o in Order.objects.all().order_by('-created_at')[:20]:
    print('\nOrder id=%s order_number=%s total_amount=%s user=%s' % (o.id, o.order_number, o.total_amount, o.user.username))
    for it in o.items.all():
        prod_name = it.product.prd_name if it.product else 'N/A'
        db_price = None
        try:
            db_price = Decimal(str(it.product.prd_price))
        except Exception:
            db_price = None
        print('  Item: %s qty=%s stored_price=%s db_price=%s total=%s' % (prod_name, it.quantity, it.price, db_price, it.get_total_price()))
