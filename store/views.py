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
from django.utils import timezone

from django.db import connection

from django.db import connection
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_ids = request.POST.getlist('product_ids')
        if not product_ids:
            messages.error(request, "Please select at least one product")
            return redirect('women')

        user_id = request.user.id

        with connection.cursor() as cursor:
            # Get or create customer
            cursor.execute("SELECT id FROM store_customer WHERE user_id = %s", [user_id])
            customer_row = cursor.fetchone()
            if customer_row:
                customer_id = customer_row[0]
            else:
                cursor.execute(
                    "INSERT INTO store_customer (user_id) OUTPUT INSERTED.id VALUES (%s)", [user_id]
                )
                customer_id = cursor.fetchone()[0]

            # Get or create cart
            cursor.execute(
                "SELECT id FROM store_cart WHERE customer_id = %s AND is_active = 1", [customer_id]
            )
            cart_row = cursor.fetchone()
            if cart_row:
                cart_id = cart_row[0]
            else:
                cursor.execute(
                    "INSERT INTO store_cart (customer_id, is_active, created_at, updated_at) "
                    "OUTPUT INSERTED.id VALUES (%s, 1, %s, %s)",
                    [customer_id, timezone.now(), timezone.now()]
                )
                cart_id = cursor.fetchone()[0]

            # Add products to cart
            for product_id in product_ids:
                cursor.execute(
                    "SELECT id FROM store_cartitem WHERE cart_id = %s AND product_id = %s",
                    [cart_id, product_id]
                )
                cart_item = cursor.fetchone()
                if cart_item:
                    cursor.execute(
                        "UPDATE store_cartitem SET quantity = quantity + 1 WHERE id = %s",
                        [cart_item[0]]
                    )
                else:
                    cursor.execute(
                        "INSERT INTO store_cartitem (cart_id, product_id, quantity) VALUES (%s, %s, 1)",
                        [cart_id, product_id]
                    )

        messages.success(request, "Products added to cart successfully")
        return redirect('cart')

    return redirect('women')


@login_required
def update_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = request.POST.get('quantity')
        user_id = request.user.id

        with connection.cursor() as cursor:
            # Verify cart item belongs to user
            cursor.execute("""
                SELECT ci.id, c.id
                FROM store_cartitem ci
                JOIN store_cart c ON ci.cart_id = c.id
                JOIN store_customer cust ON c.customer_id = cust.id
                WHERE ci.id = %s AND cust.user_id = %s
            """, [item_id, user_id])
            item = cursor.fetchone()

            if item:
                cursor.execute("UPDATE store_cartitem SET quantity = %s WHERE id = %s", [quantity, item_id])

                # Calculate subtotal and total
                cursor.execute("""
                    SELECT SUM(p.price * ci.quantity) 
                    FROM store_cartitem ci
                    JOIN store_product p ON ci.product_id = p.id
                    WHERE ci.cart_id = %s
                """, [item[1]])
                subtotal = cursor.fetchone()[0] or 0
                total = subtotal  # Add tax/delivery/discount if needed

                # Get item total
                cursor.execute("""
                    SELECT (p.price * ci.quantity)
                    FROM store_cartitem ci
                    JOIN store_product p ON ci.product_id = p.id
                    WHERE ci.id = %s
                """, [item_id])
                item_total = cursor.fetchone()[0] or 0

                return JsonResponse({
                    'item_total': f"{item_total:.2f}",
                    'subtotal': f"{subtotal:.2f}",
                    'total': f"{total:.2f}"
                })
            else:
                return JsonResponse({'error': 'Cart item not found'}, status=404)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def remove_from_cart(request, item_id):
    user_id = request.user.id
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM store_cartitem
            WHERE id = %s AND cart_id IN (
                SELECT c.id FROM store_cart c
                JOIN store_customer cust ON c.customer_id = cust.id
                WHERE cust.user_id = %s
            )
        """, [item_id, user_id])
    return redirect('cart')



def get_customer(self):
        """Helper method to get the customer profile"""
        return self.customer



from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from .models import Customer
@login_required
def cart_view(request):
    try:
        # Get the logged-in customer's record
        customer = Customer.objects.filter(user=request.user).first()
        if not customer:
            messages.error(request, "No customer profile found.")
            return redirect('home')  # Or your fallback URL

        customer_id = customer.id

        # Check if cart exists
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM store_cart WHERE customer_id = %s AND is_active = 1
            """, [customer_id])
            cart_row = cursor.fetchone()

            # If no cart, create one
            if not cart_row:
                cursor.execute("""
                    INSERT INTO store_cart (customer_id, is_active) VALUES (%s, 1)
                """, [customer_id])
                cursor.execute("""
                    SELECT id FROM store_cart WHERE customer_id = %s AND is_active = 1
                """, [customer_id])
                cart_row = cursor.fetchone()

            cart_id = cart_row[0]

            # Fetch cart items with product details
            cursor.execute("""
                SELECT ci.id, ci.product_id, ci.quantity, p.name, s.quantity AS stock_quantity, p.price, p.image
                FROM store_cartitem ci
                JOIN store_product p ON ci.product_id = p.id
                JOIN store_stock s ON p.id = s.product_id
                WHERE ci.cart_id = %s
            """, [cart_id])

            items = cursor.fetchall()

        # Build item list with correct item total
        item_list = []
        for item in items:
            item_dict = {
                'id': item[0],
                'product_id': item[1],
                'quantity': item[2],
                'product_name': item[3],
                'stock_quantity': item[4],
                'product_price': item[5],
                'item_total': item[2] * item[5],  # Quantity * Price
                'product_image_url': '/products/' + item[6].replace('products/', '')
            }
            item_list.append(item_dict)

        # Calculate subtotal (sum of item totals)
        subtotal = sum(item['item_total'] for item in item_list)
        total = subtotal  # Update this if you add tax or shipping

        cart_count = len(item_list)

        return render(request, 'cart.html', {
            'items': item_list,
            'subtotal': subtotal,
            'total': total,
            'cart_count': cart_count
        })

    except Exception as e:
        print(f"Error in cart_view: {e}")
        messages.error(request, "There was a problem loading your cart.")
        return render(request, 'cart.html', {
            'items': [],
            'subtotal': 0,
            'total': 0,
            'cart_count': 0
        })

def get_cart_count(request):
    if request.user.is_authenticated:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(ci.id) 
                FROM store_cartitem ci
                JOIN store_cart c ON ci.cart_id = c.id
                JOIN store_customer cust ON c.customer_id = cust.id
                WHERE cust.user_id = %s
            """, [request.user.id])
            cart_count = cursor.fetchone()[0]
        return cart_count
    return 0

@login_required
def checkout(request):
    try:
        customer = Customer.objects.filter(user=request.user).first()
        if not customer:
            messages.error(request, "Customer profile not found.")
            return redirect('cart')
        customer_id = customer.id

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM store_cart WHERE customer_id = %s AND is_active = 1
            """, [customer_id])
            cart_row = cursor.fetchone()
            if not cart_row:
                raise Exception("Cart not found")
            cart_id = cart_row[0]

            cursor.execute("""
                SELECT ci.id, ci.product_id, ci.quantity, p.price,p.name
                FROM store_cartitem ci
                JOIN store_product p ON ci.product_id = p.id
                WHERE ci.cart_id = %s
            """, [cart_id])
            cart_items = cursor.fetchall()

        subtotal = sum([item[2] * item[3] for item in cart_items]) if cart_items else 0
        total = subtotal


        if not cart_items:
            messages.error(request, "Your cart is empty.")
            return redirect('cart')

        item_list = [{
            'id': item[0],
            'product_id': item[1],
            'quantity': item[2],
            'total_price': item[2] * item[3],
            'name': item[4]

        } for item in cart_items]
         
         
        return render(request, 'checkout.html', {
            'cart_items': item_list,
            'cart': {'id': cart_id},
            'total': total,
        })

    except Exception as e:
        print(f"Error: {e}")
        messages.error(request, "Something went wrong with your cart.")
        return redirect('cart')


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.db import transaction, connection
from django.contrib import messages
from store.models import Customer


@login_required
def place_order(request):
    if request.method != 'POST':
        print("Request method is not POST, redirecting to checkout")
        return redirect('checkout')

    # List required POST fields here for validation
    required_fields = []

    for field in required_fields:
        if not request.POST.get(field):
            print(f"Missing required field in POST data: {field}")
            messages.error(request, f"Missing required field: {field}")
            return redirect('checkout')

    try:
        with transaction.atomic():
            user_id = request.user.id
            print(f"User ID: {user_id}")

            with connection.cursor() as cursor:
                print("Inserting billing details...")
                cursor.execute("""
                    INSERT INTO store_billingdetails 
                    (user_id, country, first_name, last_name, company_name, address, address2, city, state, zip_code, email, phone, payment_method, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE())
                """, [
                    user_id,
                    request.POST.get('country', ''),
                    request.POST.get('fname', ''),
                    request.POST.get('lname', ''),
                    request.POST.get('companyname', ''),
                    request.POST.get('address', ''),
                    request.POST.get('address2', ''),
                    request.POST.get('towncity', ''),
                    request.POST.get('stateprovince', ''),
                    request.POST.get('zippostalcode', ''),
                    request.POST.get('email', ''),
                    request.POST.get('phone', ''),
                    request.POST.get('payment_method', ''),
                ])
                print("Billing details inserted.")

                cursor.execute("SELECT TOP 1 id FROM store_billingdetails WHERE user_id = %s ORDER BY created_at DESC", [user_id])
                billing_id_row = cursor.fetchone()
                if not billing_id_row:
                    print("Failed to retrieve billing details ID.")
                    messages.error(request, "Failed to create billing details.")
                    return redirect('checkout')
                billing_id = billing_id_row[0]
                print(f"Billing ID: {billing_id}")

            customer = Customer.objects.filter(user=request.user).first()
            if not customer:
                print("Customer not found for user.")
                messages.error(request, "Customer not found.")
                return redirect('checkout')
            customer_id = customer.id
            print(f"Customer ID: {customer_id}")

            with connection.cursor() as cursor:
                print("Fetching active cart ID...")
                cursor.execute("SELECT TOP 1 id FROM store_cart WHERE customer_id = %s AND is_active = 1", [customer_id])
                cart_row = cursor.fetchone()
                if not cart_row:
                    print("No active cart found for customer.")
                    messages.error(request, "No active cart found.")
                    return redirect('cart')
                cart_id = cart_row[0]
                print(f"Cart ID: {cart_id}")

                print("Fetching cart items...")
                cursor.execute("""
                    SELECT ci.id, ci.product_id, ci.quantity
                    FROM store_cartitem ci
                    WHERE ci.cart_id = %s
                """, [cart_id])
                cart_items = cursor.fetchall()
                print(f"Number of cart items: {len(cart_items)}")

                if not cart_items:
                    print("Cart is empty.")
                    messages.error(request, "Your cart is empty.")
                    return redirect('cart')

                print("Inserting order...")
                cursor.execute("""
                    INSERT INTO store_order (customer_id, billing_details_id, total, complete, date_ordered)
                    VALUES (%s, %s, 0, 0, GETDATE())
                """, [customer_id, billing_id])
                cursor.execute("SELECT TOP 1 id FROM store_order WHERE customer_id = %s ORDER BY date_ordered DESC", [customer_id])
                order_id_row = cursor.fetchone()
                if not order_id_row:
                    print("Failed to create order.")
                    messages.error(request, "Failed to create order.")
                    return redirect('checkout')
                order_id = order_id_row[0]  # This is the raw order ID from SQL
                print(f"Order ID: {order_id}")

                total_amount = 0

                for item in cart_items:
                    cartitem_id, product_id, quantity = item
                    print(f"Processing cart item - Product ID: {product_id}, Quantity: {quantity}")

                    cursor.execute("SELECT price FROM store_product WHERE id = %s", [product_id])
                    price_row = cursor.fetchone()
                    if not price_row:
                        print(f"Product not found with ID {product_id}")
                        messages.error(request, f"Product with ID {product_id} not found.")
                        return redirect('cart')
                    price = price_row[0]

                    item_total = price * quantity
                    total_amount += item_total
                    print(f"Item total: {item_total}, Running total: {total_amount}")

                    cursor.execute("""
                        INSERT INTO store_orderitem (order_id, product_id, quantity,date_added)
                        VALUES (%s, %s, %s,%s)
                    """, [order_id, product_id, quantity,timezone.now()])
                    print(f"Inserted order item for product {product_id}")

                    cursor.execute("""
                        UPDATE store_stock SET quantity = quantity - %s WHERE product_id = %s
                    """, [quantity, product_id])
                    print(f"Updated stock for product {product_id}")

                print(f"Updating order total to: {total_amount}")
                cursor.execute("""
                    UPDATE store_order SET total = %s WHERE id = %s
                """, [total_amount, order_id])

                print(f"Deactivating cart ID: {cart_id}")
                cursor.execute("UPDATE store_cart SET is_active = 0 WHERE id = %s", [cart_id])
                print(f"Deleting cart items for cart ID: {cart_id}")
                cursor.execute("DELETE FROM store_cartitem WHERE cart_id = %s", [cart_id])

        messages.success(request, "Your order has been placed successfully!")
        print("Order placed successfully, redirecting to order_complete.")
        # Use the order_id we got from the SQL query, not order.id
        print(f"Created order with ID: {order_id}")
        return redirect('order_complete', order_id=order_id)  # Fixed this line

    except Exception as e:
        import traceback
        traceback.print_exc()  # Full traceback in console/log
        messages.error(request, f"Error placing order: {str(e)}")
        print(f"Exception caught in place_order: {e}")
        return redirect('checkout')



from django.shortcuts import render, get_object_or_404

def order_receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    ordered_items = OrderItem.objects.filter(order=order)
    
    # Calculate total if not already stored
    total_amount = sum(item.quantity * item.product.price for item in ordered_items)
    
    context = {
        'order': order,
        'ordered_items': ordered_items,
        'total_amount': total_amount,
    }
    return render(request, 'receipt.html', context)

def order_complete(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        ordered_items = OrderItem.objects.filter(order=order)
        
        context = {
            'order': order,
            'ordered_items': ordered_items,
            'total_amount': sum(item.quantity * item.product.price for item in ordered_items),
            'order_date': order.date_ordered.strftime('%B %d, %Y'),
        }
        return render(request, 'order-complete.html', context)
        
    except Order.DoesNotExist:
        return render(request, 'order-complete.html', {'error': 'Order not found'})


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
    
from django.db import connection
from django.shortcuts import render
from .models import Product

def women_view(request):
    # Base SQL query
    sql = "SELECT * FROM store_product WHERE gender = %s"
    params = ['W']

    # Get filters from request
    brand = request.GET.get('brand')
    size = request.GET.get('size')
    width = request.GET.get('width')
    style = request.GET.get('style')
    color = request.GET.get('color')
    material = request.GET.get('material')
    technology = request.GET.get('technology')

    # Dynamically build SQL query based on filters
    if brand:
        sql += " AND brand = %s"
        params.append(brand)
    if size:
        sql += " AND sizes LIKE %s"
        params.append(f"%{size}%")
    if width:
        sql += " AND width = %s"
        params.append(width)
    if style:
        sql += " AND style = %s"
        params.append(style)
    if color:
        sql += " AND colors LIKE %s"
        params.append(f"%{color}%")
    if material:
        sql += " AND material = %s"
        params.append(material)
    if technology:
        sql += " AND technologies LIKE %s"
        params.append(f"%{technology}%")

    # Execute raw SQL query
    products = Product.objects.raw(sql, params)

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
from django.shortcuts import render
from django.http import HttpResponseNotFound
from .models import Product

def product_detail(request):
    product_id = request.GET.get('product_id')
    if not product_id:
        return HttpResponseNotFound("Product ID not provided")

    try:
        product = Product.objects.raw("SELECT * FROM store_product WHERE id = %s", [product_id])[0]
    except IndexError:
        return HttpResponseNotFound("Product not found")

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



@login_required
def index(request):
    products = Product.objects.raw("SELECT TOP 16 * FROM store_product")
    best_sellers = BestSeller.objects.raw("SELECT TOP 8 * FROM best_sellers_view")
    new_arrivals = NewArrival.objects.raw("SELECT TOP 8 * FROM new_arrivals")

    return render(request, 'index.html', {
        'products': products,
        'best_sellers': best_sellers,
        'new_arrivals': new_arrivals
    })



def men(request):
    # Base SQL query
    sql = "SELECT * FROM store_product WHERE gender = %s"
    params = ['M']

    # Get filters from request
    brand = request.GET.get('brand')
    size = request.GET.get('size')
    width = request.GET.get('width')
    style = request.GET.get('style')
    color = request.GET.get('color')
    material = request.GET.get('material')
    technology = request.GET.get('technology')

    # Dynamically build SQL query based on filters
    if brand:
        sql += " AND brand = %s"
        params.append(brand)
    if size:
        sql += " AND sizes LIKE %s"
        params.append(f"%{size}%")
    if width:
        sql += " AND width = %s"
        params.append(width)
    if style:
        sql += " AND style = %s"
        params.append(style)
    if color:
        sql += " AND colors LIKE %s"
        params.append(f"%{color}%")
    if material:
        sql += " AND material = %s"
        params.append(material)
    if technology:
        sql += " AND technologies LIKE %s"
        params.append(f"%{technology}%")

    # Execute raw SQL query
    products = Product.objects.raw(sql, params)

    

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

from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login
from django.contrib.auth.models import User


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from .models import StoreUser  # Import your custom user model

from django.contrib.auth import get_user_model, login
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password, get_password_validators
from django.db import connection
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.conf import settings

User = get_user_model()

# Get user by ID (helper)
def get_user_by_id(user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, email, password, is_active, is_staff, is_superuser
            FROM store_storeuser WHERE id = %s
        """, [user_id])
        row = cursor.fetchone()
        if not row:
            return None
        user = User()
        user.id, user.username, user.email, user.password, user.is_active, user.is_staff, user.is_superuser = row
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        return user

# Get user by username (helper)
def get_user_by_username(username):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, email, password, is_active, is_staff, is_superuser
            FROM store_storeuser WHERE username = %s
        """, [username])
        row = cursor.fetchone()
        if not row:
            return None
        user = User()
        user.id, user.username, user.email, user.password, user.is_active, user.is_staff, user.is_superuser = row
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        return user

# Registration with password validation
def register(request):
    if request.method == 'POST':
        username = request.POST['username'].strip()
        email = request.POST['email'].strip()
        password = request.POST['password1']
        password_confirm = request.POST['password2']

        # Check password match
        if password != password_confirm:
            return render(request, 'registration/register.html', {'error': 'Passwords do not match'})

        # Check for existing username/email
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM store_storeuser WHERE username = %s", [username])
            if cursor.fetchone():
                return render(request, 'registration/register.html', {'error': 'Username already exists'})

            cursor.execute("SELECT id FROM store_storeuser WHERE email = %s", [email])
            if cursor.fetchone():
                return render(request, 'registration/register.html', {'error': 'Email already exists'})

        # Validate password strength
        try:
            validate_password(password, user=None, password_validators=get_password_validators(settings.AUTH_PASSWORD_VALIDATORS))
        except ValidationError as e:
            return render(request, 'registration/register.html', {'error': ' '.join(e.messages)})

        # Insert new user
        hashed_password = make_password(password)
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO store_storeuser (username, password, email, is_active, is_staff, is_superuser, date_joined)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, [username, hashed_password, email, True, False, False])
            cursor.execute("SELECT id FROM store_storeuser WHERE username = %s", [username])
            user_id = cursor.fetchone()[0]

        user = get_user_by_id(user_id)
        login(request, user)
        return redirect('home')

    return render(request, 'registration/register.html')

# Login with failure messages
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username'].strip()
        password = request.POST['password']

        user = get_user_by_username(username)
        if user:
            if not user.is_active:
                return render(request, 'registration/login.html', {'error': 'Account is inactive. Contact support.'})
            if check_password(password, user.password):
                login(request, user)
                return redirect('/admin/' if user.is_superuser else 'home')
            else:
                return render(request, 'registration/login.html', {'error': 'Incorrect password. Please try again.'})
        else:
            return render(request, 'registration/login.html', {'error': 'User does not exist. Please check your username.'})

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

#signals

@receiver(post_save, sender=Product)
def create_stock_for_product(sender, instance, created, **kwargs):
    if created:
        Stock.objects.create(product=instance, quantity=64)

@receiver(post_save, sender=Product)
def create_product_details(sender, instance, created, **kwargs):
    if created:
        ProductDetails.objects.create(product=instance)

@receiver(post_save, sender=StoreUser)
def create_customer_for_new_user(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)      