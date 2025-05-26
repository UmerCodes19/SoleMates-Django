document.addEventListener('DOMContentLoaded', function () {
    const quantityInputs = document.querySelectorAll('.quantity-input');

    quantityInputs.forEach(input => {
        input.addEventListener('input', () => {
            const max = parseInt(input.dataset.max);
            const val = parseInt(input.value);

            if (val > max) {
                alert(`Only ${max} item(s) in stock.`);
                input.value = max;
            } else if (val < 1 || isNaN(val)) {
                input.value = 1;
            }
        });
    });
});