from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Product, Customer, Order, OrderItem, Stock, Cart, CartItem, User, ProductDetails,BillingDetails,StoreUser




class ProductDetailsInline(admin.StackedInline):
    model = ProductDetails
    extra = 0  # Don't show empty extra forms
    fieldsets = [
        ('Descriptions', {
            'fields': [
                'short_description', 
                'full_description',
                'manufacturer_info'
            ]
        }),
        ('Specifications', {
            'fields': [
                'weight',
                'dimensions',
                'features',
                'care_instructions'
            ]
        }),
        ('Media', {
            'fields': [
                'image_2',
                
            ]
        }),
        ('Ratings', {
            'fields': [
                'average_rating',
                'review_count'
            ]
        }),
    ]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductDetailsInline]
    list_display = ('name', 'brand', 'price', 'gender', 'style', 'purchase_count')
    list_filter = ('brand', 'gender', 'style', 'width')
    search_fields = ('name', 'colors', 'technologies')
    readonly_fields = ('purchase_count',)

@admin.register(ProductDetails)
class ProductDetailsAdmin(admin.ModelAdmin):
    list_display = ('product', 'average_rating', 'review_count')
    search_fields = ('product__name',)
    raw_id_fields = ('product',)  # Better for performance with many products

# Register other models
admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Stock)
admin.site.register(StoreUser)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(BillingDetails)
admin.site.register(User, UserAdmin)