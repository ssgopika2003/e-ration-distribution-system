from django.shortcuts import render

# Create your views here.
from django.templatetags.static import static
from django.shortcuts import redirect
from django.contrib import messages
from .forms import RegistrationForm
from .forms import ShopOwnerRegistrationForm
import re
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db import transaction
from django import forms
from .models import Category, Product, Profile, Cart, FamilyMember
from .models import CardType, Order, OrderItem, Notification
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from .utils import notify_user


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['catgory_name']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['prd_name', 'prd_des', 'prd_price', 'category', 'prd_image', 'quantity']


def staff_required(view_func):
    # Only allow staff users who are NOT superusers (shop owners).
    return user_passes_test(lambda u: u.is_staff and not u.is_superuser)(view_func)


def staff_or_admin_required(view_func):
    """Allow access to staff users or superusers.

    Use this on views that both shop-owners (is_staff) and site-admins (is_superuser)
    should be able to access (view/edit/delete products and users).
    """
    return user_passes_test(lambda u: u.is_authenticated and (u.is_staff or u.is_superuser))(view_func)


def home(request):
    """Render homepage with featured ration items and products from the database."""
    # Get products with images for the slideshow, limit to 6 for performance
    products_with_images = Product.objects.filter(prd_image__isnull=False).exclude(prd_image='')[:6]
    # Get all products for the products section
    all_products = Product.objects.all()
    return render(request, 'home.html', {
        "products": products_with_images,
        "all_products": all_products
    })


def register(request):
    """Simple user registration using Django's UserCreationForm."""
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            # after saving profile, validate and create FamilyMember records if provided
            try:
                profile = Profile.objects.get(user=user)
            except Profile.DoesNotExist:
                profile = None
            member_errors = []
            if profile:
                # remove any previous members
                profile.members.all().delete()
                family_count = 0
                try:
                    family_count = int(request.POST.get('family_members') or 0)
                except ValueError:
                    family_count = 0
                for i in range(family_count):
                    name = (request.POST.get(f'member_name_{i}') or '').strip()
                    gender = request.POST.get(f'member_gender_{i}') or None
                    dob = request.POST.get(f'member_dob_{i}') or None
                    # require a name for each member
                    if not name:
                        member_errors.append(f'Member {i+1}: name is required.')
                    else:
                        # attempt to create member; let Django validate dob parsing
                        try:
                            FamilyMember.objects.create(profile=profile, name=name, gender=gender or None, dob=dob or None)
                        except Exception as e:
                            member_errors.append(f'Member {i+1}: invalid data ({e})')
            # if member errors, add non-field error to form and re-render
            if member_errors:
                # rollback created members
                if profile:
                    profile.members.all().delete()
                form.add_error(None, 'Errors in family member data: ' + '; '.join(member_errors))
                return render(request, 'register.html', {'form': form})
            # Use a different message level to avoid showing on homepage
            messages.add_message(request, messages.SUCCESS, f'Account created successfully! Welcome {user.username}! Please log in to continue.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})


def shop_owner_register(request):
    if request.method == 'POST':
        form = ShopOwnerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shop owner account created successfully. Please login.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ShopOwnerRegistrationForm()
    return render(request, 'shop_owner/register.html', {'form': form})


def login_view(request):
    """Authenticate user credentials and redirect based on role using AuthenticationForm."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Log the user in
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            # Role-based redirects
            if user.is_superuser:
                return redirect('site_admin_dashboard')
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('user_profile')
        # if form invalid, fall through and re-render with errors
    else:
        form = AuthenticationForm(request)
    # Render login page with the form (contains errors when POST invalid)
    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    """Log the user out and redirect to home."""
    username = request.user.username
    messages.info(request, f'You have been logged out successfully. Goodbye, {username}!')
    logout(request)
    return redirect('home')


@staff_required
def admin_dashboard(request):
    """Render the admin dashboard with overview cards."""
    products_count = Product.objects.count()
    categories_count = Category.objects.count()
    users_count = Profile.objects.count()

    
    context = {
        'title': 'Kerala Ration Shop Admin',
        'subtitle': 'Manage ration items, orders, customers & reports all in one place.',
        'products_count': products_count,
        'categories_count': categories_count,
        'users_count': users_count,
    }
    return render(request, 'shop_owner/dashboard.html', context)


@login_required
def user_profile(request):
    """Render the user profile view."""
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None
    categories = Category.objects.all()
    members = profile.members.all() if profile else []
    return render(request, 'user/profile.html', {'profile': profile, 'categories': categories, 'members': members})


@login_required
def edit_profile(request):
    """Handle user profile editing."""
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    # Maximum allowed family members editable in the UI
    FAMILY_MEMBERS_MAX = 20
    
    if request.method == 'POST':
        profile.address = request.POST.get('address', '')
        # normalize contact number to digits only
        contact = request.POST.get('contact_no', '')
        profile.contact_no = re.sub(r'[^0-9]', '', contact)
        profile.ration_card_number = request.POST.get('ration_card_number', profile.ration_card_number)
        profile.place = request.POST.get('place', profile.place)
        # ration card images
        if 'ration_card_front' in request.FILES:
            profile.ration_card_front = request.FILES['ration_card_front']
        if 'ration_card_back' in request.FILES:
            profile.ration_card_back = request.FILES['ration_card_back']
        # profile image
        if 'image' in request.FILES:
            profile.image = request.FILES['image']

        # handle family members editing: expect fields member_name_i, member_gender_i, member_dob_i
        # simple validation: name required; dob cannot be in the future
        members_to_create = []
        member_errors = []
        try:
            family_count = int(request.POST.get('family_members') or 0)
        except ValueError:
            family_count = 0
        # enforce maximum
        if family_count > FAMILY_MEMBERS_MAX:
            messages.error(request, f'Maximum {FAMILY_MEMBERS_MAX} family members allowed.')
            family_count = FAMILY_MEMBERS_MAX
        for i in range(family_count):
            name = (request.POST.get(f'member_name_{i}') or '').strip()
            gender = request.POST.get(f'member_gender_{i}') or None
            dob_str = request.POST.get(f'member_dob_{i}') or None
            
            # Parse date properly
            dob = None
            if dob_str and dob_str.strip():
                try:
                    from datetime import datetime, date
                    dob = datetime.strptime(dob_str.strip(), '%Y-%m-%d').date()
                    # Validate that DOB is not in the future
                    if dob > date.today():
                        member_errors.append(f'Member {i+1}: Date of birth cannot be in the future')
                        continue
                except ValueError:
                    member_errors.append(f'Member {i+1}: Invalid date format')
                    continue
            
            if not name:
                member_errors.append(f'Member {i+1}: name is required')
            else:
                members_to_create.append((name, gender, dob))

        if member_errors:
            for err in member_errors:
                messages.error(request, err)
        else:
            # delete existing and create new members
            profile.members.all().delete()
            for name, gender, dob in members_to_create:
                FamilyMember.objects.create(profile=profile, name=name, gender=gender or None, dob=dob or None)
        profile.save()
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('user_profile')
    
    categories = Category.objects.all()
    return render(request, 'user/edit_profile.html', {'profile': profile, 'categories': categories, 'family_max': FAMILY_MEMBERS_MAX})


# ----------------- User pages -----------------


@login_required
def user_dashboard(request):
    """User landing/dashboard page for ration shop."""
    # simple set of featured ration items
    products = Product.objects.all()[:6]
    categories = Category.objects.all()
    return render(request, 'user/dashboard.html', {'products': products, 'categories': categories})


@login_required
def notifications_list(request):
    """List notifications for the logged-in user."""
    notes = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    # Choose template based on role
    if request.user.is_staff and not request.user.is_superuser:
        tpl = 'shop_owner/notifications.html'
        ctx = {'notifications': notes}
    else:
        tpl = 'user/notifications.html'
        ctx = {'notifications': notes, 'categories': Category.objects.all()}
    return render(request, tpl, ctx)


@login_required
def notifications_mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    # Redirect back to dashboard or referer
    next_url = request.META.get('HTTP_REFERER') or 'user_dashboard'
    return redirect(next_url)


@login_required
def categories_dropdown(request):
    """Return categories for the dropdown include (used in user_nav)."""
    categories = Category.objects.all()
    return render(request, 'user/_categories_dropdown.html', {'categories': categories})


@login_required
def category_products(request, category_id):
    cat = get_object_or_404(Category, pk=category_id)
    products = Product.objects.filter(category=cat)
    categories = Category.objects.all()
    return render(request, 'user/category_products.html', {'category': cat, 'products': products, 'categories': categories})


@login_required
def user_product_detail(request, product_id):
    """User-facing product detail view."""
    product = get_object_or_404(Product, pk=product_id)
    categories = Category.objects.all()
    return render(request, 'user/product_detail.html', {'product': product, 'categories': categories})


@staff_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.catgory_name}" has been added successfully!')
            # Stay on the same page to show the success message
            form = CategoryForm()  # Reset form for new entry
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = CategoryForm()
    return render(request, 'shop_owner/add_category.html', {'form': form})


@staff_required
def add_product(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            # record which shop owner created the product (staff users only)
            if request.user.is_staff:
                product.owner = request.user
            product.save()
            messages.success(request, f'Product "{product.prd_name}" has been added successfully!')
            # Stay on the same page to show the success message
            form = ProductForm()  # Reset form for new entry
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = ProductForm()
    return render(request, 'shop_owner/add_product.html', {'form': form, 'categories': categories})


@staff_or_admin_required
def view_products(request):
    query = request.GET.get('q', '').strip()
    qs = Product.objects.select_related('category').all()
    if query:
        qs = qs.filter(prd_name__icontains=query)
    context = {'products': qs, 'q': query}
    return render(request, 'shop_owner/view_products.html', context)


@staff_or_admin_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    # Superusers should see the admin-styled product detail page
    if request.user.is_superuser:
        return render(request, 'admin/product_detail.html', {'product': product})
    return render(request, 'shop_owner/product_detail.html', {'product': product})


@staff_or_admin_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    categories = Category.objects.all()
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.prd_name}" has been updated successfully!')
            return redirect('view_products')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = ProductForm(instance=product)
    return render(request, 'shop_owner/edit_product.html', {'form': form, 'product': product, 'categories': categories})


@staff_or_admin_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        product_name = product.prd_name
        product.delete()
        messages.success(request, f'Product "{product_name}" has been deleted successfully!')
        return redirect('view_products')
    # Render admin-styled delete confirm for superusers
    if request.user.is_superuser:
        return render(request, 'admin/delete_product.html', {'product': product})
    return render(request, 'shop_owner/delete_product.html', {'product': product})


@staff_or_admin_required
def user_detail(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = None
    # Superusers get admin-styled user detail
    if request.user.is_superuser:
        return render(request, 'admin/user_detail.html', {'user': user, 'profile': profile})
    return render(request, 'shop_owner/user_detail.html', {'user': user, 'profile': profile})


@staff_or_admin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" has been deleted successfully!')
        return redirect('view_users')
    # Superusers should see admin delete confirm
    if request.user.is_superuser:
        return render(request, 'admin/delete_user.html', {'user': user})
    return render(request, 'shop_owner/delete_user.html', {'user': user})


@staff_or_admin_required
def view_users(request):
    # Only show regular customers (non-staff users), not shop owners
    card_type_id = request.GET.get('card_type')
    card_types = CardType.objects.all()
    users_qs = Profile.objects.select_related('user').filter(user__is_staff=False)
    if card_type_id:
        users_qs = users_qs.filter(card_type__id=card_type_id)
    return render(request, 'shop_owner/view_users.html', {'users': users_qs, 'card_types': card_types, 'selected_card_type': card_type_id})


# ----------------- Cart functionality -----------------

@login_required
def add_to_cart(request, product_id):
    """Add a ration item to the user's cart with quantity management."""
    # Use transaction to update inventory atomically
    with transaction.atomic():
        product = Product.objects.select_for_update().get(pk=product_id)
        if product.quantity <= 0:
            messages.error(request, f'Sorry, {product.prd_name} is currently out of stock!')
            return redirect('user_product_detail', product_id=product_id)
        cart_item, created = Cart.objects.select_for_update().get_or_create(user=request.user, product=product)
        if not created:
            # If adding one would exceed stock
            if cart_item.quantity + 1 > product.quantity:
                messages.error(request, f'Only {product.quantity} units of {product.prd_name} are available!')
                return redirect('user_product_detail', product_id=product_id)
            cart_item.quantity += 1
            cart_item.save()
            # decrement product stock
            product.quantity -= 1
            product.save()
            messages.success(request, f'Quantity updated for {product.prd_name} in your cart!')
        else:
            cart_item.quantity = 1
            cart_item.save()
            product.quantity -= 1
            product.save()
            messages.success(request, f'{product.prd_name} has been added to your cart!')
    return redirect('user_product_detail', product_id=product_id)


@login_required
def cart_page(request):
    """Display the user's cart."""
    cart_items = Cart.objects.filter(user=request.user)
    categories = Category.objects.all()
    count = Cart.objects.filter(user=request.user).count()
    total_price = sum(item.total_price() for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'categories': categories,
        'count': count,
    }
    return render(request, 'user/cart.html', context)


@login_required
def remove_from_cart(request, cart_item_id):
    """Remove a ration item from the user's cart."""
    with transaction.atomic():
        cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
        # restore product stock by the cart_item quantity
        product = Product.objects.select_for_update().get(pk=cart_item.product.pk)
        product.quantity += (cart_item.quantity or 0)
        product.save()
        product_name = cart_item.product.prd_name
        cart_item.delete()
        messages.success(request, f'{product_name} has been removed from your cart!')
    return redirect('cart_page')


@login_required
def update_cart_quantity(request, cart_item_id):
    """Update the quantity of a ration item in the cart."""
    if request.method == 'POST':
        with transaction.atomic():
            cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
            new_qty = int(request.POST.get('quantity', 1))
            product = Product.objects.select_for_update().get(pk=cart_item.product.pk)
            if new_qty <= 0:
                # remove and restore stock
                product.quantity += (cart_item.quantity or 0)
                product.save()
                cart_item.delete()
                messages.success(request, f'{cart_item.product.prd_name} has been removed from your cart!')
            else:
                # compute delta and validate
                delta = new_qty - (cart_item.quantity or 0)
                if delta > 0 and delta > product.quantity:
                    messages.error(request, f'Only {product.quantity} more units available for {product.prd_name}!')
                    return redirect('cart_page')
                # apply changes
                product.quantity -= delta
                product.save()
                cart_item.quantity = new_qty
                cart_item.save()
                messages.success(request, f'Quantity updated for {cart_item.product.prd_name}!')
    return redirect('cart_page')

@login_required
def decrease(request, cartitem_id):
    """Decrease quantity of a ration item in the cart by 1."""
    with transaction.atomic():
        cart_item = get_object_or_404(Cart, id=cartitem_id, user=request.user)
        product = Product.objects.select_for_update().get(pk=cart_item.product.pk)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            # restore one unit back to stock
            product.quantity += 1
            product.save()
            messages.success(request, f'Quantity decreased for {cart_item.product.prd_name}!')
        else:
            # restore entire quantity and remove
            product.quantity += (cart_item.quantity or 0)
            product.save()
            cart_item.delete()
            messages.success(request, f'{cart_item.product.prd_name} has been removed from your cart!')
    return redirect('cart_page')


# --- Site administrator (superuser) views ---
def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@admin_required
def site_admin_dashboard(request):
    """Superuser dashboard: lists shop owners, regular users and products with quick actions."""
    # Shop owners = staff users who are not superuser
    shop_owners = User.objects.filter(is_staff=True, is_superuser=False)
    # Regular users via Profile
    users = Profile.objects.select_related('user').filter(user__is_staff=False)
    products = Product.objects.all()
    carts = Cart.objects.all()
    # Counts for dashboard cards
    products_count = products.count()
    shop_owners_count = shop_owners.count()
    customers_count = users.count()
    carts_count = carts.count()

    context = {
        'shop_owners': shop_owners,
        'users': users,
        'products': products,
        'products_count': products_count,
        'shop_owners_count': shop_owners_count,
        'customers_count': customers_count,
        'carts_count': carts_count,
    }
    return render(request, 'admin/index.html', context)


@admin_required
def admin_edit_user(request, user_id):
    """Allow superuser to edit a user's profile (address/contact/image)."""
    user = get_object_or_404(User, pk=user_id)
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=user)

    if request.method == 'POST':
        profile.address = request.POST.get('address', profile.address)
        contact = request.POST.get('contact_no', profile.contact_no)
        profile.contact_no = re.sub(r'[^0-9]', '', contact)
        profile.ration_card_number = request.POST.get('ration_card_number', profile.ration_card_number)
        profile.place = request.POST.get('place', profile.place)
        if 'image' in request.FILES:
            profile.image = request.FILES['image']
        profile.save()
        messages.success(request, f'Profile for {user.username} updated.')
        # After saving, return to the admin-styled user detail page
        return redirect('admin_user_detail', user_id=user.id)

    return render(request, 'admin/edit_user.html', {'user': user, 'profile': profile})


@admin_required
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" has been deleted.')
        return redirect('site_admin_dashboard')
    return render(request, 'admin/delete_user.html', {'user': user})


@admin_required
def admin_view_users(request):
    """List all regular users for superuser to view/edit/delete."""
    from django.db.models import Count
    users = (
        Profile.objects
        .select_related('user', 'card_type')
        .filter(user__is_staff=False)
        .annotate(order_count=Count('user__orders'))
    )
    return render(request, 'admin/view_users.html', {'users': users})


@admin_required
def admin_view_shop_owners(request):
    """List shop owners (staff non-superusers)."""
    shop_owners = User.objects.filter(is_staff=True, is_superuser=False)
    return render(request, 'admin/view_shop_owners.html', {'shop_owners': shop_owners})


@admin_required
def admin_user_detail(request, user_id):
    """Superuser-specific user detail page (admin-styled)."""
    user = get_object_or_404(User, pk=user_id)
    profile = (
        Profile.objects.select_related('card_type')
        .prefetch_related('members')
        .filter(user=user)
        .first()
    )

    # Prefetch user's orders with items and products to display purchase details
    orders = Order.objects.filter(user=user).prefetch_related('items__product')
    # If the viewed user is a shop owner, show their added products
    owner_products = None
    if user.is_staff and not user.is_superuser:
        owner_products = Product.objects.filter(owner=user).select_related('category')

    return render(request, 'admin/user_detail.html', {
        'user': user,
        'profile': profile,
        'orders': orders,
        'owner_products': owner_products,
    })


@admin_required
def admin_owner_detail(request, user_id):
    """Superuser page focused on shop-owner details and their products."""
    owner = get_object_or_404(User, pk=user_id, is_staff=True)
    profile = (
        Profile.objects.select_related('card_type')
        .filter(user=owner)
        .first()
    )
    products = Product.objects.filter(owner=owner).select_related('category')
    return render(request, 'admin/ownerdetails.html', {
        'owner': owner,
        'profile': profile,
        'products': products,
    })


@admin_required
def admin_view_products(request):
    """List products for admin with edit/delete actions."""
    products = Product.objects.select_related('category').all()
    return render(request, 'admin/view_products.html', {'products': products})


@admin_required
def admin_send_stock_alerts(request):
    """Send low-stock alerts to shop owners based on item type thresholds.

    Thresholds:
    - Rice items < 50 kg
    - Oil items < 20 litre
    - Flour items < 25 (kg)

    Assumptions:
    - Product.prd_name contains case-insensitive keywords: 'rice', 'oil', or 'flour'
    - Product.owner is set to the shop owner (staff user) who added it
    """
    # Define thresholds and matching keywords
    RULES = [
        { 'keyword': 'rice', 'threshold': 50, 'unit': 'kg' },
        { 'keyword': 'oil', 'threshold': 20, 'unit': 'litre' },
        { 'keyword': 'flour', 'threshold': 25, 'unit': 'kg' },
    ]

    alerts_sent = 0
    from django.db.models import Q
    for rule in RULES:
        low_items = (
            Product.objects
            .filter(
                Q(prd_name__icontains=rule['keyword']) | Q(category__catgory_name__icontains=rule['keyword']),
                quantity__lt=rule['threshold'],
                owner__isnull=False,
            )
            .select_related('owner')
        )

        for item in low_items:
            subject = f"Low stock alert: {item.prd_name}"
            msg = (
                f"Your item '{item.prd_name}' is low on stock. Current quantity: "
                f"{item.quantity} {rule['unit']} (threshold {rule['threshold']} {rule['unit']}). "
                "Please restock soon."
            )
            link_url = reverse('product_detail', args=[item.id])
            notify_user(recipient=item.owner, subject=subject, message=msg, link_url=link_url, send_email=True, send_sms=False)
            alerts_sent += 1

    if alerts_sent:
        messages.success(request, f"{alerts_sent} low-stock alert(s) sent to shop owners.")
    else:
        messages.info(request, "No low-stock items found matching the alert rules.")

    # Redirect back to site admin dashboard
    return redirect('site_admin_dashboard')


@admin_required
def admin_send_product_alert(request, product_id):
    """Send a low-stock alert for a single product to its owner if it matches rules.

    Rules:
    - keyword 'rice' threshold 50 kg
    - keyword 'oil' threshold 20 litre
    - keyword 'flour' threshold 25 kg

    If the product doesn't have an owner or doesn't match any rule/threshold, a message is shown.
    Redirects back to owner details if possible, otherwise to admin products list.
    """
    product = get_object_or_404(Product, pk=product_id)

    # Fallback redirect
    redirect_target = 'admin_view_products'
    if product.owner and product.owner.is_staff:
        redirect_target = ('admin_owner_detail', {'user_id': product.owner.id})

    # Mapping of keyword rules
    rules = [
        { 'keyword': 'rice', 'threshold': 50, 'unit': 'kg' },
        { 'keyword': 'oil', 'threshold': 20, 'unit': 'litre' },
        { 'keyword': 'flour', 'threshold': 25, 'unit': 'kg' },
    ]

    name_l = (product.prd_name or '').lower()
    cat_l = ''
    try:
        cat_l = (product.category.catgory_name or '').lower()
    except Exception:
        cat_l = ''
    matched = None
    for r in rules:
        if r['keyword'] in name_l or r['keyword'] in cat_l:
            matched = r
            break

    if not product.owner:
        messages.error(request, 'Cannot send alert: this product has no owner assigned.')
    elif not matched:
        messages.info(request, 'No alert rule matched for this product name.')
    elif product.quantity is None:
        messages.error(request, 'Cannot send alert: product has no quantity set.')
    elif product.quantity >= matched['threshold']:
        messages.info(request, f"No alert sent. Current quantity ({product.quantity} {matched['unit']}) is above threshold ({matched['threshold']} {matched['unit']}).")
    else:
        link_url = reverse('product_detail', args=[product.id])
        notify_user(
            recipient=product.owner,
            subject=f"Low stock alert: {product.prd_name}",
            message=(
                f"Your item '{product.prd_name}' is low on stock. Current quantity: "
                f"{product.quantity} {matched['unit']} (threshold {matched['threshold']} {matched['unit']}). "
                "Please restock soon."
            ),
            link_url=link_url,
            send_email=True,
            send_sms=False,
        )
        messages.success(request, 'Low-stock alert sent to the owner.')

    # Redirect
    if isinstance(redirect_target, tuple):
        viewname, kwargs = redirect_target
        return redirect(viewname, **kwargs)
    return redirect(redirect_target)


@login_required
def increase(request, cartitem_id):
    """Increase quantity of a ration item in the cart by 1."""
    cart_item = get_object_or_404(Cart, id=cartitem_id, user=request.user)
    
    # Check if adding one more would exceed available quantity
    if cart_item.quantity + 1 > cart_item.product.quantity:
        messages.error(request, f'Only {cart_item.product.quantity} units of {cart_item.product.prd_name} are available!')
    else:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f'Quantity increased for {cart_item.product.prd_name}!')
    
    return redirect('cart_page')


@login_required
@require_http_methods(["GET", "POST"])
def checkout(request):
    """Render and handle a simple checkout form for ration items.
    On POST: clear the user's cart and show a success modal.
    """
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.info(request, 'Your cart is empty. Add ration items before checking out.')
        return redirect('cart_page')

    if request.method == 'POST':
        # Get cart details and form data
        cart_count = cart_items.count()
        total_items = sum(item.quantity for item in cart_items)
        total_amount = sum(item.quantity * item.product.prd_price for item in cart_items)
        
        # Create Order record
        import uuid
        from .models import Order, OrderItem
        
        order = Order.objects.create(
            user=request.user,
            order_number=f"ORD{uuid.uuid4().hex[:8].upper()}",
            full_name=request.POST.get('full_name', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            payment_method=request.POST.get('payment', 'cod'),
            total_amount=total_amount
        )
        
        # Create OrderItem records
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.prd_price
            )
        
        # Clear the cart
        Cart.objects.filter(user=request.user).delete()
        
        # Add success message
        messages.success(request, f'🎉 Order #{order.order_number} placed successfully! {total_items} items from {cart_count} products have been ordered. Thank you for shopping with us!')
        
        return render(request, 'user/checkout.html', {
            'show_success': True,
            'categories': Category.objects.all(),
            'order_summary': {
                'order_number': order.order_number,
                'total_products': cart_count,
                'total_items': total_items,
                'total_amount': total_amount,
            }
        })

    return render(request, 'user/checkout.html', {
        'categories': Category.objects.all(),
    })


@login_required
def order_history(request):
    """Show user's order history with purchased product details."""
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    return render(request, 'user/order_history.html', {
        'orders': orders,
        'categories': Category.objects.all(),
    })


@login_required
def order_detail(request, order_id):
    """Show detailed view of a specific order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'user/order_detail.html', {
        'order': order,
        'categories': Category.objects.all(),
    })
