document.addEventListener('DOMContentLoaded', () => {
    const checkboxes = document.querySelectorAll('.item-checkbox');
    const quantities = document.querySelectorAll('.item-quantity');
    const totalAmountElement = document.getElementById('total-amount');
  
    // Function to update the total price
    function updateTotal() {
      let total = 0;
  
      checkboxes.forEach((checkbox, index) => {
        if (checkbox.checked) {
          const quantity = parseInt(quantities[index].value, 10) || 1;
          const price = parseFloat(checkbox.getAttribute('data-price'));
          total += price * quantity;
        }
      });
  
      totalAmountElement.textContent = total.toFixed(2);
    }
  
    // Add event listeners to checkboxes and quantity inputs
    checkboxes.forEach((checkbox) => {
      checkbox.addEventListener('change', updateTotal);
    });
  
    quantities.forEach((quantity) => {
      quantity.addEventListener('input', updateTotal);
    });
  });
  