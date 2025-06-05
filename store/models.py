# store/models.py
from django.utils import timezone  #
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from shoestore import settings

class User(AbstractUser):
    is_customer = models.BooleanField(default=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)


    
    # Add these to resolve the reverse accessor clashes
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="store_user_groups",
        related_query_name="store_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="store_user_permissions",
        related_query_name="store_user",
    )

    def __str__(self):
        return self.username

class Product(models.Model):

    BRAND_CHOICES = [
        ('NIKE', 'Nike'),
        ('ADIDAS', 'Adidas'),
        ('MERREL', 'Merrel'),
        ('GUCCI', 'Gucci'),
        ('SKECHERS', 'Skechers'),
    ]
    
    MATERIAL_CHOICES = [
        ('LEATHER', 'Leather'),
        ('SUEDE', 'Suede'),
        ('MESH', 'Mesh'),
        ('RUBBER', 'Rubber'),
    ]
    
    # Add these fields
    
    GENDER_CHOICES = [('M', 'Men'), ('W', 'Women'), ('U', 'Unisex')]
    STYLE_CHOICES = [
        ('RUN', 'Running'), ('CAS', 'Casual'), 
        ('FOR', 'Formal'), ('SPO', 'Sports')
    ]
    WIDTH_CHOICES = [('S', 'Standard'), ('W', 'Wide'), ('N', 'Narrow')]
    
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=10, choices=BRAND_CHOICES, blank=True, null=True)
    material = models.CharField(max_length=10, choices=MATERIAL_CHOICES, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES,default='Unisex')
    style = models.CharField(max_length=3, choices=STYLE_CHOICES , default='Casual')
    sizes = models.CharField(max_length=100, help_text="Comma separated sizes (6,7,8)",default=0)
    width = models.CharField(max_length=1, choices=WIDTH_CHOICES,default='Standard')
    colors = models.CharField(max_length=200,default='Black')
    technologies = models.CharField(max_length=200, blank=True,default='N/A')
    purchase_count = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
    
    def get_available_sizes(self):
        """Helper method to get sizes as list"""
        return [size.strip() for size in self.sizes.split(',')] if self.sizes else []
    
    def get_available_widths(self):
        """Helper method to get width choices"""
        return dict(self.WIDTH_CHOICES)
    
    def get_images(self):
        return self.image.url if self.image else None

class ProductDetails(models.Model):
    product = models.OneToOneField(
        Product, 
        on_delete=models.CASCADE,
        related_name='details'
    )
    
    # Description fields
    short_description = models.TextField(blank=True, default='')
    full_description = models.TextField(blank=True, default='')
    manufacturer_info = models.TextField(blank=True, default='')
    
    # Technical specifications
    weight = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight in grams"
    )
    dimensions = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Format: LxWxH in cm"
    )
    
    # Images
    image_2 = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True
    )
    
    
    # Ratings
    average_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    review_count = models.PositiveIntegerField(default=0)
    
    # Additional features
    features = models.TextField(
        blank=True,
        default='',
        help_text="Bullet point features (one per line)"
    )
    
    # Care instructions
    care_instructions = models.TextField(blank=True, default='')
    
    # Shipping info
    shipping_info = models.TextField(
        blank=True,
        default='',
        help_text="Shipping and return policy information"
    )
    
    def __str__(self):
        return f"Details for {self.product.name}"
    
    def get_features_list(self):
        """Convert features text to bullet point list"""
        return self.features.split('\n') if self.features else []


class Customer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)


    def __str__(self):
        return self.user.username


class BillingDetails(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    country = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=0)
    transaction_id = models.CharField(max_length=100, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    billing_details = models.ForeignKey(BillingDetails, on_delete=models.CASCADE)


    def __str__(self):
        return str(self.id)
    
    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total

class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def get_total(self):
        return self.product.price * self.quantity 

class Stock(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} in stock"
    


    # models.py
class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)  # Change this to Customer
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    @property
    def get_total(self):
        return self.product.price * self.quantity 

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def get_cart_items(self):
        return sum(item.quantity for item in self.orderitem_set.all())
    
    

from django.core.exceptions import ValidationError

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.product.price * self.quantity

    def clean(self):
        stock = Stock.objects.filter(product=self.product).first()
        if stock and self.quantity > stock.quantity:
            raise ValidationError(f"Cannot add more than {stock.quantity} items of this product to the cart.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


        #Views

class BestSeller(models.Model):
    product_id = models.IntegerField(primary_key=True)
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_image_url = models.CharField(max_length=500)
    total_purchases = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'best_sellers_view'


class UserProfileView(models.Model):
    user_id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=150)
    product_image_url = models.CharField(max_length=500) 
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    customer_id = models.IntegerField()
    product_id = models.IntegerField(null=True)
    product_name = models.CharField(max_length=255, null=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    date_ordered = models.DateTimeField(null=True)

    class Meta:
        managed = False  # Important! Since this is a SQL view
        db_table = 'user_profile_view'

class SearchProduct(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    image = models.CharField(max_length=500) 
    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.CharField(max_length=255)
    material = models.CharField(max_length=255)
    gender = models.CharField(max_length=50)
    style = models.CharField(max_length=255)
    sizes = models.TextField()  # Assuming multiple sizes stored as text (e.g., JSON or comma-separated)
    colors = models.TextField()  # Same assumption
    technologies = models.TextField()  # Same assumption

    class Meta:
        managed = False  # It's a view, not a real table
        db_table = 'search_products_view'

class RelatedProducts(models.Model):
    base_product_id = models.IntegerField()
    related_product_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=10, choices=Product.BRAND_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.CharField(max_length=100)  # Stores the image path
    gender = models.CharField(max_length=1, choices=Product.GENDER_CHOICES)
    style = models.CharField(max_length=3, choices=Product.STYLE_CHOICES)
    similarity_score = models.IntegerField()
    material = models.CharField(max_length=10, choices=Product.MATERIAL_CHOICES, blank=True, null=True)
    colors = models.CharField(max_length=200)
    
    class Meta:
        managed = False  # Tells Django this is a read-only model for a database view
        db_table = 'related_products_view'

class NewArrival(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_image_url = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField()

    class Meta:
        managed = False  # Important: Django won’t manage the view's table
        db_table = 'new_arrivals'

# triggers related
      
class ProductAudit(models.Model):
    action_time = models.DateTimeField()
    action_type = models.CharField(max_length=10)
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255, null=True)
    quantity = models.IntegerField(null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    stock_before = models.IntegerField(null=True)
    stock_after = models.IntegerField(null=True)

    class Meta:
        db_table = 'product_audit'



class StockAudit(models.Model):
    action_time = models.DateTimeField()
    action_type = models.CharField(max_length=10)
    stock_id = models.IntegerField()
    product_id = models.IntegerField(null=True)
    quantity_before = models.IntegerField(null=True)
    quantity_after = models.IntegerField(null=True)
    last_updated = models.DateTimeField(null=True)
    product_name = models.CharField(max_length=255, null=True, blank=True)


    class Meta:
        db_table = 'stock_audit'


class OrderAudit(models.Model):
    action_time = models.DateTimeField()
    action_type = models.CharField(max_length=10)
    order_id = models.IntegerField()
    customer_id = models.IntegerField(null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    date_ordered = models.DateTimeField(null=True)
    orderitem_id = models.IntegerField(null=True)
    product_id = models.IntegerField(null=True)
    quantity = models.IntegerField(null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    class Meta:
        db_table = 'order_audit'


# AUTH USER RELATED

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class StoreUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class StoreUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now) 
    # Add fields as needed to match your table
    # e.g. first_name, last_name, etc.

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = StoreUserManager()

    def __str__(self):
        return self.username

      