// Function to filter products based on brand
function filterProducts(brand) {
    const products = document.querySelectorAll('.product');
  
    products.forEach(product => {
      // Show all products if the filter is set to 'all'
      if (brand === 'all') {
        product.style.display = 'block';
      } else {
        // Check if the product matches the selected brand
        const productBrand = product.getAttribute('data-brand');
        if (productBrand === brand) {
          product.style.display = 'block';
        } else {
          product.style.display = 'none';
        }
      }
    });
  }
// Store cart items (in a real implementation, this could be done using localStorage or a backend database)
let cartItems = [];

// Function to update cart count display
function updateCartCount() {
  const cartCount = document.getElementById('cart-count');
  cartCount.textContent = cartItems.length; // Update the cart count
}

// Function to handle adding items to the cart
function addToCart(productName) {
  cartItems.push(productName);
  updateCartCount();
}

// Example of adding a product to the cart (for each product, you'd call this function)
document.querySelectorAll('.add-to-cart').forEach(button => {
  button.addEventListener('click', function() {
    const productName = this.closest('.product').querySelector('h3').textContent;
    addToCart(productName);
  });
});