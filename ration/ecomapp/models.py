from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Profile(models.Model):
	user=models.ForeignKey(User,on_delete=models.CASCADE,null=True)
	# card type (APL/BPL/AAY/PHH) for filtering by shop owners
	card_type = models.ForeignKey('CardType', null=True, blank=True, on_delete=models.SET_NULL)
	address=models.CharField(max_length=255,null=True, blank=True)
	contact_no=models.CharField(max_length=15,null=True, blank=True)
	# 11-digit ration card number shown in registration UI
	ration_card_number = models.CharField(max_length=32, null=True, blank=True)
	# number of family members (adults + children)
	family_members = models.IntegerField(null=True, blank=True, help_text="Total family members")
	# ration card images: front and back
	ration_card_front = models.ImageField(upload_to="ration_cards/", null=True, blank=True)
	ration_card_back = models.ImageField(upload_to="ration_cards/", null=True, blank=True)
	# place / city / locality
	place = models.CharField(max_length=255, null=True, blank=True)
	# shop owner specific fields
	shop_license_number = models.CharField(max_length=32, null=True, blank=True)
	shop_address = models.CharField(max_length=255, null=True, blank=True)
	image=models.ImageField(upload_to="image/",null=True,blank=True)

	def __str__(self):
		username = self.user.username if self.user else "Unknown"
		return f"{username}"


class Category(models.Model):
	catgory_name=models.CharField(max_length=255,null=True)

	def __str__(self):
		return self.catgory_name or "Unnamed Category"


class Product(models.Model):
	category=models.ForeignKey(Category,on_delete=models.CASCADE,null=True)
	prd_name=models.CharField(max_length=255,null=True)
	prd_des=models.CharField(max_length=255,null=True)
	prd_price=models.IntegerField(null=True)
	prd_image=models.ImageField(upload_to="pridmage/",null=True,blank=True)
	quantity=models.IntegerField(default=0, help_text="Available quantity in stock")
	# The shop owner (staff user) who added this product
	owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='products_added')

	def __str__(self):
		name = self.prd_name or "Unnamed Product"
		return name
	
	def is_available(self):
		"""Check if product is available (quantity > 0)"""
		return self.quantity > 0
	
	def reduce_quantity(self, amount):
		"""Reduce quantity by specified amount"""
		if self.quantity >= amount:
			self.quantity -= amount
			self.save()
			return True
		return False

class Cart(models.Model):
	user=models.ForeignKey(User,on_delete=models.CASCADE,null=True)
	product=models.ForeignKey(Product,on_delete=models.CASCADE,null=True)
	quantity=models.IntegerField(null=True)
	
	def total_price(self):
		return self.product.prd_price * self.quantity


class FamilyMember(models.Model):
	"""Individual family members linked to a Profile.

	Stored separately so we can keep names, gender and DOB for each member.
	"""
	profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='members')
	name = models.CharField(max_length=255)
	gender = models.CharField(max_length=16, null=True, blank=True)
	dob = models.DateField(null=True, blank=True)

	def __str__(self):
		return self.name


class CardType(models.Model):
	"""Represents ration card categories with a friendly name and a colour for UI filtering.

	Examples: APL (white), BPL (pink), AAY (yellow), PHH (cream)
	"""
	code = models.CharField(max_length=16, unique=True)
	name = models.CharField(max_length=64)
	color = models.CharField(max_length=32, null=True, blank=True, help_text='CSS color or class')

	def __str__(self):
		return f"{self.name} ({self.code})"


class Order(models.Model):
	"""Represents a completed order placed by a user."""
	STATUS_CHOICES = [
		('pending', 'Pending'),
		('processing', 'Processing'),
		('shipped', 'Shipped'),
		('delivered', 'Delivered'),
		('cancelled', 'Cancelled'),
	]
	
	PAYMENT_CHOICES = [
		('upi', 'UPI'),
		('netbanking', 'Net Banking'),
		('cod', 'Cash on Delivery'),
	]
	
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
	order_number = models.CharField(max_length=32, unique=True)
	full_name = models.CharField(max_length=255)
	email = models.EmailField()
	phone = models.CharField(max_length=15)
	address = models.TextField()
	payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	total_amount = models.DecimalField(max_digits=10, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-created_at']
	
	def __str__(self):
		return f"Order #{self.order_number} by {self.user.username}"


class OrderItem(models.Model):
	"""Individual items within an order."""
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.IntegerField()
	price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
	
	def __str__(self):
		return f"{self.quantity}x {self.product.prd_name} in Order #{self.order.order_number}"
	
	def get_total_price(self):
		return self.quantity * self.price


class Notification(models.Model):
	"""Simple in-app notification for users (shop owners).

	Used by admin to alert owners about low stock thresholds.
	"""
	recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
	subject = models.CharField(max_length=255)
	message = models.TextField()
	# Optional deep link to view more details (e.g., product detail URL path)
	link_url = models.CharField(max_length=255, null=True, blank=True)
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"To {self.recipient.username}: {self.subject}"



