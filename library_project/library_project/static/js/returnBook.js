function returnBook(book_decimal, new_status=2) {
    // Perform AJAX request to Django backend using fetch



    // console.log(JSON.stringify({book_id:book_decimal}))
    fetch('/check-status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // You may need to include additional headers like CSRF token
            'X-CSRFToken': csrfToken // Define getCSRFToken() function
        },
        body: JSON.stringify({book_decimal:book_decimal, new_status:new_status})
    })
    .then(response => {
        // user not logged in redirect
        if (response.redirected === true) {
            alert("Must be logged in as an admin to books. Redirecting to login page.");
            window.location.href = response.url;
            return response.json();
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
        return null;
    } else if (response.success) {
        alert('Book found successfully!');
        // location.reload();
        console.log(response.book_status)
    } else if (response.failed) {
        alert('Book not found in checkout table');
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