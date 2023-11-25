function checkoutBook(decimalCode) {
    // Perform AJAX request to Django backend using fetch
    fetch('/checkout-book/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // You may need to include additional headers like CSRF token
            'X-CSRFToken': csrfToken // Define getCSRFToken() function
        },
        body: JSON.stringify({"DecimalCode":decimalCode}),
    })
    .then(response => response.json())
    .then(data => {
        // Handle the response from the Django backend
        handleCheckoutResponse(data);
    })
    .catch(error => {
        console.error('Error during fetch request:', error);
    });
}

function handleCheckoutResponse(response) {
    // Assuming the Django backend sends a JSON response
    // You may need to adjust this based on your actual backend response format
    if (response.success) {
        // Book successfully checked out
        alert('Book checked out successfully!');
    } else if (response.waitlisted) {
        // User added to the waitlist
        alert('You have been added to the waitlist for this book.');
    } else if (response.permission_denied) {
        // User doesn't have permission to check out the book
        alert('You do not have permission to check out this book.');
    } else if (response.not_logged_in) {
        // User is not logged in
        alert('Please log in to check out the book.');
        // You may redirect the user to the login page, for example
        window.location.href = '/login/';
    } else {
        // Handle other cases as needed
        alert('Unexpected response from the server.');
    }
}

// Example function to get CSRF token, adjust as needed
function getCSRFToken() {
    const csrfCookie = document.cookie.split('; ')
        .find(cookie => cookie.startsWith('csrftoken='));
    return csrfCookie ? csrfCookie.split('=')[1] : '';
}
