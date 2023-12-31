function checkoutBook(bookID) {
    // Perform AJAX request to Django backend using fetch
    console.log(JSON.stringify({book_id:bookID}))
    fetch('/checkout-book/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // You may need to include additional headers like CSRF token
            'X-CSRFToken': csrfToken // Define getCSRFToken() function
        },
        body: JSON.stringify({book_id:bookID}),
    })
    .then(response => {
        // user not logged in redirect
        if (response.redirected === true) {
            alert("Must be logged in to check out the book. Redirecting to login page.")
            window.location.href = response.url;
            return response.json()
        } else {
            return response.json();
        }
    })
    .then(data => {
        // Handle the response from the Django backend
        handleCheckoutResponse(data);
    })
    .catch(error => {
        console.error('Error during fetch request:', error);
    });
}
function handleCheckoutResponse(response) {
    if (response === null) {
        return;
    } else if (response.success) {
        alert('Book checked out successfully!');
        location.reload();
    } else if (response.waitlisted) {
        alert('You have been added to the waitlist for this book.');
        location.reload();
    } else if (response.permission_denied) {
        alert('You do not have permission to check out this book.');
    } else {
        // Check for a redirect status code (e.g., 302 Found)
        if (response.redirect) {
            // Perform a redirect
            window.location.href = response.redirect;
        } else {
            // Handle other cases as needed
            alert('Unexpected response from the server.');
        }
    }
}