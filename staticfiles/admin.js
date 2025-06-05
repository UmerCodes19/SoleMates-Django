document.addEventListener('DOMContentLoaded', function() {
    // Highlight admin header with a subtle animation
    const header = document.getElementById('header');
    if (header) {
      header.style.transition = 'transform 0.5s ease-in-out';
      header.addEventListener('mouseover', () => {
          header.style.transform = 'scale(1.05)';
      });
      header.addEventListener('mouseout', () => {
          header.style.transform = 'scale(1)';
      });
    }

    // Animate button clicks
    const buttons = document.querySelectorAll('input[type="submit"], .button');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            btn.style.transform = 'scale(0.95)';
            setTimeout(() => btn.style.transform = 'scale(1)', 200);
        });
    });

    // Chart.js sales chart (if canvas exists)
    const ctx = document.getElementById('salesChart');
    if (ctx) {
      // Replace this static data with dynamic data from Django if needed
      const salesChart = new Chart(ctx.getContext('2d'), {
          type: 'line',
          data: {
              labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
              datasets: [{
                  label: 'Sales ($)',
                  data: [120, 150, 180, 90, 200, 230, 170],
                  borderColor: '#ff4d6d',
                  backgroundColor: 'rgba(255, 77, 109, 0.2)',
                  fill: true,
                  tension: 0.4,
              }]
          },
          options: {
              responsive: true,
              scales: {
                  y: { beginAtZero: true }
              }
          }
      });
    }
});
