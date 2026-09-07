from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
	path('', views.home, name='home'),
	path('register/', views.register, name='register'),
	path('shop-owner/register/', views.shop_owner_register, name='shop_owner_register'),
	path('login/', views.login_view, name='login'),
	path('logout/', views.logout_view, name='logout'),

	# Admin pages (use non-conflicting path so Django admin site doesn't capture it)
	path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

	# Site administrator (superuser) area
	path('site-admin/', views.site_admin_dashboard, name='site_admin_dashboard'),
	path('site-admin/user/<int:user_id>/edit/', views.admin_edit_user, name='admin_edit_user'),
	path('site-admin/user/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
	path('site-admin/user/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
	path('site-admin/owner/<int:user_id>/', views.admin_owner_detail, name='admin_owner_detail'),
	path('site-admin/users/', views.admin_view_users, name='admin_view_users'),
	path('site-admin/shop-owners/', views.admin_view_shop_owners, name='admin_view_shop_owners'),
	path('site-admin/products/', views.admin_view_products, name='admin_view_products'),
	path('site-admin/actions/send-stock-alerts/', views.admin_send_stock_alerts, name='admin_send_stock_alerts'),
	path('site-admin/product/<int:product_id>/send-alert/', views.admin_send_product_alert, name='admin_send_product_alert'),

	# Admin management (add routes removed — only shop owners should add)
	path('add_category/', views.add_category, name='add_category'),
	path('add_product/', views.add_product, name='add_product'),
	path('view_products/', views.view_products, name='view_products'),
	path('product/<int:product_id>/', views.product_detail, name='product_detail'),
	path('product/<int:product_id>/edit/', views.edit_product, name='edit_product'),
	path('product/<int:product_id>/delete/', views.delete_product, name='delete_product'),
	path('view_users/', views.view_users, name='view_users'),
	path('user/<int:user_id>/', views.user_detail, name='user_detail'),
	path('user/<int:user_id>/delete/', views.delete_user, name='delete_user'),

	# User pages
	path('profile/', views.user_profile, name='user_profile'),
	path('profile/edit/', views.edit_profile, name='edit_profile'),

	# user pages
	path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
	path('notifications/', views.notifications_list, name='notifications_list'),
	path('notifications/mark-all-read/', views.notifications_mark_all_read, name='notifications_mark_all_read'),
	path('cart/', views.cart_page, name='cart_page'),
	path('categories/', views.categories_dropdown, name='categories'),
	path('categories/<int:category_id>/', views.category_products, name='category_products'),
	path('product/<int:product_id>/detail/', views.user_product_detail, name='user_product_detail'),
	
	# cart functionality
	path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
	path('remove-from-cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
	path('update-cart/<int:cart_item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/decrease/<int:cartitem_id>/', views.decrease, name='cart_decrease'),
    path('cart/increase/<int:cartitem_id>/', views.increase, name='cart_increase'),

    # checkout
    path('checkout/', views.checkout, name='checkout'),
    
    # Order history
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
]