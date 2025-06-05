$(document).ready(function () {
    $('.quantity-input').on('change', function () {
        var input = $(this);
        var form = input.closest('form');
        var itemDiv = input.closest('.product-cart');
        var itemTotalSpan = itemDiv.find('.item-total');

        $.ajax({
            url: form.attr('action'),
            method: 'POST',
            data: form.serialize(),
            headers: {
                'X-CSRFToken': form.find('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function (data) {
                // Update the item total and cart totals
                itemTotalSpan.text(`$${data.item_total}`);
                $('#subtotal').text(`$${data.subtotal}`);
                $('#total').text(`$${data.total}`);
            },
            error: function () {
                alert("Failed to update cart. Please try again.");
            }
        });
    });

    // Handle item removal with AJAX
    $('.closed').on('click', function (e) {
        e.preventDefault();
        var url = $(this).attr('href');
        var itemDiv = $(this).closest('.product-cart');

        $.ajax({
            url: url,
            method: 'GET',
            success: function () {
                itemDiv.remove(); // Remove from DOM
                location.reload(); // Or update total via AJAX
            }
        });
    });
});
