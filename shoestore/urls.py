"""
URL configuration for shoestore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin

from django.conf import settings
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.urls import path
from django.views.generic.base import RedirectView
from store import views
from django.urls import re_path
from django.views.static import serve
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),
    path('index/', views.index, name='index'),
    
    path('men/', views.men, name='men'),
    path('women.html', views.women_view, name='women'),
        path('men.html', views.men, name='men'),

    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
     path('update-cart/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('', RedirectView.as_view(url='/login/', permanent=False)),
      path('cart.html', views.cart_view, name='cart'),
        path('cart.html', views.cart_view, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('women/', views.women_view, name='women'),
        path('men/', views.men, name='men'),
# urls.py
path('cart/update/', views.update_cart, name='update_cart'),

    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/', views.cart_view, name='cart'),
    path('update_cart/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
     path('checkout/', views.checkout, name='proceed_to_checkout'),
    path('checkout.html', views.checkout, name='proceed_to_checkout'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout.html', views.checkout, name='checkout'),
    path('order-complete/', views.order_complete, name='order_complete'),
    path('order-complete.html', views.order_complete, name='order_complete'),
   # Remove duplicate URLs and keep this one:
   path('product-detail.html', views.product_detail, name='product_detail'),

path('product-detail/', views.product_detail, name='product_detail'),
path('product-detail/<int:id>/', views.product_detail, name='product-detail'),
# urls.py
path('product-detail/', views.product_detail, name='product_detail'),
path('login/', views.user_login, name='login'),
path('profile/', views.profile_view, name='profile'),
path('profile/update/', views.update_profile, name='update_profile'),
path('search/', views.search_view, name='search'),
path('register/', views.register, name='register'),
path('place-order/', views.place_order, name='place_order'),
 path('product/', views.product_detail, name='product_detail'),
path('order-complete/<int:billing_id>/', views.order_complete, name='order-complete'),
path('order_complete/<int:billing_id>/', views.order_complete, name='order-complete')








    
]

if settings.DEBUG:
    urlpatterns += [
       re_path(r'^(?P<path>products/.*)$', serve, {'document_root': settings.MEDIA_ROOT})
    ]