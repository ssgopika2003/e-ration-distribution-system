from django.contrib import admin
from .models import CardType, Profile, Category, Product, Cart, FamilyMember, Order, OrderItem, Notification


@admin.register(CardType)
class CardTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'color']
    list_filter = ['color']
    search_fields = ['code', 'name']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'card_type', 'ration_card_number', 'family_members', 'place']
    list_filter = ['card_type']
    search_fields = ['user__username', 'ration_card_number', 'place']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['catgory_name']
    search_fields = ['catgory_name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['prd_name', 'category', 'prd_price', 'quantity', 'is_available']
    list_filter = ['category']
    search_fields = ['prd_name']
    list_editable = ['prd_price', 'quantity']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'total_price']
    list_filter = ['user']


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'profile', 'gender', 'dob']
    list_filter = ['gender']
    search_fields = ['name']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'get_total_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__username', 'full_name', 'email']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    def save_model(self, request, obj, form, change):
        if not obj.order_number:
            import uuid
            obj.order_number = f"ORD{uuid.uuid4().hex[:8].upper()}"
        super().save_model(request, obj, form, change)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'get_total_price']
    list_filter = ['order__created_at']
    search_fields = ['order__order_number', 'product__prd_name']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'subject', 'link_url', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['recipient__username', 'subject', 'message']
