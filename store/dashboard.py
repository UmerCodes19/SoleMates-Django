from jet.dashboard.dashboard import Dashboard
from jet.dashboard.modules import DashboardModule, LinkList, ModelList
from django.db.models import Sum
from .models import Product, Order, Customer

class CustomIndexDashboard(Dashboard):
    def init_with_context(self, context):
        print("Dashboard init_with_context started")

        request = context.get('request')
        if not request:
            print("Warning: No request in context")

        # Quick Links
        self.children.append(LinkList(
            'Quick Links',
            layout='inline',
            children=[
                {'title': 'Site Home', 'url': '/'},
                {'title': 'Admin Home', 'url': '/admin/'},
            ]
        ))

        # Models Overview
        self.children.append(ModelList(
            'Management',
            models=['store.models.Product', 'store.models.Order', 'store.models.Customer']
        ))

        try:
            total_products = Product.objects.count()
            total_orders = Order.objects.count()
            total_customers = Customer.objects.count()
            total_sales = Order.objects.aggregate(total=Sum('total'))['total'] or 0

            print(f"Fetched Data - Products: {total_products}, Orders: {total_orders}, Customers: {total_customers}, Sales: {total_sales}")
        except Exception as e:
            print("Error fetching data from DB:", e)
            # Use fallback values in case of error
            total_products = total_orders = total_customers = 0
            total_sales = 0.0

        stats_module = DashboardModule(
            title='Site Statistics',
            children=[
                f'Total Products: {total_products}',
                f'Total Orders: {total_orders}',
                f'Total Customers: {total_customers}',
                f'Total Sales: ${total_sales:.2f}',
            ],
            layout='stacked',
        )
        self.children.append(stats_module)

        print("Dashboard init_with_context finished")
