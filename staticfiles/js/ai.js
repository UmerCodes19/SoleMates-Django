document.addEventListener('DOMContentLoaded', function() {

    // Reusable function for a product section
    function setupProductSection(containerId, buttonId, formId, countId) {
        const productContainer = document.getElementById(containerId);
        const addToCartBtn = document.getElementById(buttonId);
        const cartForm = document.getElementById(formId);
        const countElement = document.getElementById(countId);
        let selectedProducts = [];

        // Initialize button as hidden
        addToCartBtn.style.display = 'none';

        // Product selection logic
        productContainer.addEventListener('click', function(e) {
            if (e.target.closest('.product-info-btn') || e.target.closest('a') || e.target.closest('button')) {
                return;
            }

            const productCard = e.target.closest('.product-card');
            if (!productCard) return;

            const productId = productCard.dataset.productId;

            productCard.classList.toggle('selected');

            if (productCard.classList.contains('selected')) {
                selectedProducts.push(productId);
            } else {
                selectedProducts = selectedProducts.filter(id => id !== productId);
            }

            updateProductForm(selectedProducts);
            updateAddToCartButton(selectedProducts.length);
        });

        function updateProductForm(selectedIds) {
    // Remove any existing hidden inputs first
    cartForm.querySelectorAll('input[name="product_ids"]').forEach(el => el.remove());

    // Create one hidden input per product id
    selectedIds.forEach(id => {
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'product_ids';
        hiddenInput.value = id;
        cartForm.appendChild(hiddenInput);
    });
}

        function updateAddToCartButton(count) {
            countElement.textContent = count;
            addToCartBtn.style.display = count > 0 ? 'block' : 'none';
        }

        // Form submission validation
        cartForm.addEventListener('submit', function(e) {
            if (selectedProducts.length === 0) {
                e.preventDefault();
                alert('Please select at least one product');
            }
        });
    }

    // Call the function for each section with different IDs
    setupProductSection('product-container', 'add-to-cart-btn', 'cart-form', 'selected-count');
    setupProductSection('product-container2', 'add-to-cart-btn2', 'cart-form2', 'selected-count2');
    setupProductSection('product-container3', 'add-to-cart-btn3', 'cart-form3', 'selected-count3');

});
