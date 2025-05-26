$(document).ready(function() {
  $('.menu-link').click(function(e) {
    e.preventDefault();

    const $this = $(this);
    const targetSection = $this.data('section');
const $currentSection = $('.product-section:visible, .product-section2:visible');
    const currentSectionId = $currentSection.attr('id');

    if (targetSection === currentSectionId) return; // Already visible

    // Update active tab styling
    $('.menu-link').removeClass('active');
    $this.addClass('active');

    // Animate fade out current section
    $currentSection.addClass('animated fadeOut').one('animationend', function() {
      $(this).hide().removeClass('animated fadeOut');

      // Animate fade in target section
      const $target = $('#' + targetSection);
      $target.show().addClass('animated fadeIn').one('animationend', function() {
        $(this).removeClass('animated fadeIn');
      });
    });
  });
});
