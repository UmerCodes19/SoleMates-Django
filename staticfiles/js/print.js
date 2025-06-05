document.getElementById('print-ebill-btn').addEventListener('click', function() {
    // Get data from attributes
    const btn = document.getElementById('print-ebill-btn');
    const userFirst = btn.getAttribute('data-user-first');
    const userLast = btn.getAttribute('data-user-last');
    const userEmail = btn.getAttribute('data-user-email');
    const orderDate = btn.getAttribute('data-order-date');
    const orderTotal = btn.getAttribute('data-order-total');
    
    // Collect order items
    const orderItems = [];
    document.querySelectorAll('.order-item').forEach(item => {
        orderItems.push({
            name: item.getAttribute('data-name'),
            quantity: item.getAttribute('data-quantity'),
            price: item.getAttribute('data-price')
        });
    });
    
    // Generate items HTML
    let itemsHtml = '';
    orderItems.forEach(item => {
        itemsHtml += `
        <tr>
            <td>${item.name}</td>
            <td>${item.quantity}</td>
            <td>$${parseFloat(item.price).toFixed(2)}</td>
            <td>$${(item.quantity * item.price).toFixed(2)}</td>
        </tr>
        `;
    });
    
    // Prepare receipt content
    const receiptHtml = `
    <html>
    <head>
        <title>E-Bill Receipt</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { text-align: center; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #333; padding: 8px; text-align: left; }
            th { background-color: #eee; }
            .logo { text-align: center; margin-bottom: 20px; }
            .thank-you { text-align: center; margin-top: 30px; font-style: italic; }
        </style>
    </head>
    <body>
        <div class="logo">
            <h1>SoleMates</h1>
            <p>Love at First Step!</p>
        </div>
        
        <h2>Billing Information</h2>
        <p><strong>Name:</strong> ${userFirst} ${userLast}</p>
        <p><strong>Email:</strong> ${userEmail}</p>
        <p><strong>Order Date:</strong> ${orderDate}</p>

        <h2>Ordered Products</h2>
        <table>
            <thead>
                <tr>
                    <th>Product Name</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                ${itemsHtml}
            </tbody>
        </table>

        <h3>Total Amount: $${parseFloat(orderTotal).toFixed(2)}</h3>
        
        <div class="thank-you">
            <p>Thank you for your purchase!</p>
            <p>Please keep this receipt for your records</p>
        </div>
    </body>
    </html>
    `;

    // Open new window for printing
    const printWindow = window.open('', '_blank', 'height=600,width=800');
    printWindow.document.write(receiptHtml);
    printWindow.document.close();
    
    // Focus and print after content loads
    printWindow.onload = function() {
        printWindow.print();
    };
});

// Set up print button handler
document.addEventListener('DOMContentLoaded', function() {
    const printBtn = document.getElementById('print-ebill-btn');
    if (printBtn) {
        printBtn.addEventListener('click', function() {
            const orderId = this.getAttribute('data-order-id');
            window.open(
                '/receipt/' + orderId + '/',
                'receipt',
                'width=800,height=600'
            );
        });
    }
});