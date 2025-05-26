from urllib import request
from django.contrib import messages
from django.dispatch import receiver
from django.shortcuts import get_object_or_404, render,redirect
from django.db.models import Q  

from .models import Customer, NewArrival, Product, RelatedProducts, SearchProduct, User , Order,OrderItem,BillingDetails,ProductDetails,Stock,BestSeller,UserProfileView
from .models import Cart
from .models import CartItem
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponse

from django.views.decorators.http import require_POST
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile

# views.py
# views.py
from django.contrib.auth.decorators import login_required

from store import models

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_ids = request.POST.getlist('product_ids')
        if not product_ids:
            messages.error(request, "Please select at least one product")
            return redirect('women')
        
        # Get the User instance from request
        user = request.user
        
        # Get or create Customer - ensure we're using the User instance
        customer, created = Customer.objects.get_or_create(user=user)
        
        # Get or create Cart for this customer
        cart, created = Cart.objects.get_or_create(customer=customer, is_active=True)
        
        for product_id in product_ids:
            product = get_object_or_404(Product, id=product_id)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': 1}
            )
            if not created:
                cart_item.quantity += 1
                cart_item.save()
        
        messages.success(request, "Products added to cart successfully")
        return redirect('cart')
    
    return redirect('women')


@login_required
def update_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = request.POST.get('quantity')

        try:
            item = CartItem.objects.get(id=item_id, cart__customer=request.user.customer)
            item.quantity = int(quantity)
            item.save()

            cart = item.cart
            subtotal = sum(i.total_price for i in cart.items.all())
            total = subtotal  # Add tax/delivery/discount logic if needed

            return JsonResponse({
                'item_total': f"{item.total_price:.2f}",
                'subtotal': f"{subtotal:.2f}",
                'total': f"{total:.2f}"
            })

        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'Cart item not found'}, status=404)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def remove_from_cart(request, item_id):
    try:
        # Get the customer first
        customer = request.user.customer
        item = CartItem.objects.get(id=item_id, cart__customer=customer)
        item.delete()
    except (Customer.DoesNotExist, CartItem.DoesNotExist):
        pass
    return redirect('cart')  # Changed from 'cart.html' to 'cart'


def get_customer(self):
        """Helper method to get the customer profile"""
        return self.customer


@login_required
def cart_view(request):
    try:
        # Get the customer's active cart
        customer = request.user.customer
        cart = Cart.objects.get(customer=customer, is_active=True)
        items = cart.items.all()
        cart_count = items.count()

        # Attach stock quantity to each item
        for item in items:
            item.stock = Stock.objects.get(product=item.product)

        # Calculate subtotal by summing each item's total price
        subtotal = sum(item.total_price for item in items)
        
        # Add any logic for shipping or discounts here if needed
        total = subtotal  # Add shipping/discount logic here if needed

    except (Customer.DoesNotExist, Cart.DoesNotExist):
        items = []
        subtotal = 0
        total = 0
        cart_count = 0

    return render(request, 'cart.html', {
        'items': items,
        'subtotal': subtotal,
        'total': total,
        'cart_count': cart_count
    })


def get_cart_count(request):
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user).count()
    return 0


from .models import Order, CartItem

@login_required
def checkout(request):
    try:
        customer = request.user.customer
        cart = Cart.objects.get(customer=customer, is_active=True)
        cart_items = cart.items.all()

        if not cart_items:
            messages.error(request, "Your cart is empty.")
            return redirect('cart.html')

        return render(request, 'checkout.html', {
            'cart_items': cart_items,
            'cart': cart,  # Add this line to use cart.total_price in template
        })

    except (Customer.DoesNotExist, Cart.DoesNotExist):
        messages.error(request, "Something went wrong with your cart.")
        return redirect('cart')



@login_required
def place_order(request):
    if request.method == 'POST':
        # Define the required fields you expect from the form
        required_fields = [
            
            # 'country', 'fname', 'lname', 'address', 'towncity', 'stateprovince', 
            # 'zippostalcode', 'email', 'phone', 'payment_method'
        ]
        
        # Check for missing fields
        for field in required_fields:
            if not request.POST.get(field):
                messages.error(request, f"Missing required field: {field}")
                return redirect('checkout')

        # Create BillingDetails instance
        billing = BillingDetails.objects.create(
            user=request.user,
            country=request.POST['country'],
            first_name=request.POST['fname'],
            last_name=request.POST['lname'],
            company_name=request.POST.get('companyname', ''),  # optional field
            address=request.POST['address'],
            address2=request.POST.get('address2', ''),         # optional field
            city=request.POST['towncity'],
            state=request.POST['stateprovince'],
            zip_code=request.POST['zippostalcode'],
            email=request.POST['email'],
            phone=request.POST['phone'],
            payment_method=request.POST['payment_method'],
        )

        # Get customer and active cart
        customer = request.user.customer
        try:
            cart = Cart.objects.get(customer=customer, is_active=True)
        except Cart.DoesNotExist:
            messages.error(request, "No active cart found.")
            return redirect('cart')

        cart_items = cart.items.all()
        if not cart_items:
            messages.error(request, "Your cart is empty.")
            return redirect('cart')



        # Create Order
        order = Order.objects.create(customer=customer, billing_details=billing)

        total_amount = 0
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )
            total_amount += item.total_price

            # Optional: Update stock (for PostgreSQL triggers you may skip this)
            stock = Stock.objects.get(product=item.product)
            stock.quantity -= item.quantity
            stock.save()

        # Finalize the order total
        order.total = total_amount
        order.save()

        # Deactivate the cart
        cart.is_active = False
        cart.save()

        # Optional: Clear cart items if needed
        cart.items.all().delete()

        messages.success(request, "Your order has been placed successfully!")
        return redirect('order_complete')

    else:
        return redirect('checkout')


def order_complete(request):
     return render(request, 'order-complete.html')

# def print_ebill(request, billing_id):
#     billing = get_object_or_404(BillingDetails, id=billing_id)

#     html_string = render_to_string('pdf_ebill.html', {'billing': billing})
    
#     # Generate PDF in memory
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'inline; filename=receipt_{billing_id}.pdf'
    
#     with tempfile.NamedTemporaryFile(delete=True) as output:
#         HTML(string=html_string).write_pdf(target=output.name)
#         output.seek(0)
#         response.write(output.read())

#     return response


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')  # Add any additional fields you want
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user    
    
def women_view(request):
    products = Product.objects.filter(gender='W')
    


    # Get filters
    brand = request.GET.get('brand')
    size = request.GET.get('size')
    width = request.GET.get('width')
    style = request.GET.get('style')
    color = request.GET.get('color')
    material = request.GET.get('material')
    technology = request.GET.get('technology')
    
    # Apply filters only if field exists
    if brand:
        products = products.filter(brand=brand)
    if size:
        products = products.filter(sizes__contains=size)
    if width:
        products = products.filter(width=width)
    if style:
        products = products.filter(style=style)
    if color:
        products = products.filter(colors__icontains=color)
    if material:
        products = products.filter(material=material)
    if technology:
        products = products.filter(technologies__icontains=technology)
    

    

    context = {
        'products': products,
        'brand_choices': Product.BRAND_CHOICES,
        'material_choices': Product.MATERIAL_CHOICES,
        'current_brand': brand,
        'current_size': size,
        'current_width': width,
        'current_style': style,
        'current_color': color,
        'current_material': material,
        'current_technology': technology,
    }
    
    return render(request, 'women.html', context)


from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseNotFound
from .models import Product  # or your model name
def product_detail(request):
    product_id = request.GET.get('product_id')
    if not product_id:
        return HttpResponseNotFound("Product ID not provided")

    product = get_object_or_404(Product, id=product_id)

    context = {
        'product': product,
        'sizes': product.get_available_sizes(),  # your custom method
        'widths': product.get_available_widths()
            # your custom method
    }

    return render(request, 'product-detail.html', context)

@login_required
def index(request):
    products = Product.objects.all()[:16]
    best_sellers = BestSeller.objects.all()[:8]
    new_arrivals = NewArrival.objects.all()[:8]
    return render(request, 'index.html', {
        'products': products,
        'best_sellers': best_sellers,
        'new_arrivals': new_arrivals
    })

def men(request):
    products = Product.objects.filter(gender='M')
    


    # Get filters
    brand = request.GET.get('brand')
    size = request.GET.get('size')
    width = request.GET.get('width')
    style = request.GET.get('style')
    color = request.GET.get('color')
    material = request.GET.get('material')
    technology = request.GET.get('technology')
    
    # Apply filters only if field exists
    if brand:
        products = products.filter(brand=brand)
    if size:
        products = products.filter(sizes__contains=size)
    if width:
        products = products.filter(width=width)
    if style:
        products = products.filter(style=style)
    if color:
        products = products.filter(colors__icontains=color)
    if material:
        products = products.filter(material=material)
    if technology:
        products = products.filter(technologies__icontains=technology)
    

    

    context = {
        'products': products,
        'brand_choices': Product.BRAND_CHOICES,
        'material_choices': Product.MATERIAL_CHOICES,
        'current_brand': brand,
        'current_size': size,
        'current_width': width,
        'current_style': style,
        'current_color': color,
        'current_material': material,
        'current_technology': technology,
    }
    
    return render(request, 'men.html', context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
    return render(request, 'registration/login.html')




#views related

@login_required
def profile_view(request):
    user = request.user
    # Assuming you have a user profile model (customize this query as needed)
    user_info = user  # If using a custom profile model, get it here
    recent_purchases = UserProfileView.objects.filter(user_id=request.user.id).order_by('-date_ordered')[:8]
 
    return render(request, 'profile.html', {
        'user_info': user_info,
        'recent_purchases': recent_purchases,
    })

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, "Profile updated successfully!")
    return redirect('profile')  # Replace 'profile_view' with your profile view's URL name

def search_view(request):
    query = request.GET.get('q', '').strip()  # Strip removes spaces
    products = []

    
    if query:
        products = SearchProduct.objects.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(material__icontains=query) |
            Q(gender__icontains=query) |
            Q(style__icontains=query) |
            Q(sizes__icontains=query) |
            Q(colors__icontains=query) |
            Q(technologies__icontains=query)
        )
    else:
        products = []  # Empty list for empty query, no products shown

    return render(request, 'search.html', {'products': products, 'query': query})

def product_detail(request):
    product_id = request.GET.get('product_id')
    if not product_id:
        return HttpResponseNotFound("Product ID not provided")

    product = get_object_or_404(Product, id=product_id)
    
    # Get related products (limit to 4 most similar)
    related_products = RelatedProducts.objects.filter(
        base_product_id=product_id
    ).order_by('-similarity_score')[:4]
    
    # Get the actual Product objects for the related products
    related_product_objects = Product.objects.filter(
        id__in=[rp.related_product_id for rp in related_products]
    )

    context = {
        'product': product,
        'sizes': product.get_available_sizes(),
        'widths': product.get_available_widths(),
        'related_products': related_product_objects
    }

    return render(request, 'product-detail.html', context)

#signals

@receiver(post_save, sender=Product)
def create_stock_for_product(sender, instance, created, **kwargs):
    if created:
        Stock.objects.create(product=instance, quantity=64)

@receiver(post_save, sender=Product)
def create_product_details(sender, instance, created, **kwargs):
    if created:
        ProductDetails.objects.create(product=instance)

@receiver(post_save, sender=User)
def create_customer_for_new_user(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)        