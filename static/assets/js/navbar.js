
// Function to check login status and return true or false
function checkLoginStatus() {
    var isUserLoggedIn = getCookie("is_logged_in");
    return !!isUserLoggedIn; // Return true if is_logged_in exists, false if it doesn't
}

// Function to get a cookie by name (you can keep this as it is)
function getCookie(name) {
    var cookies = document.cookie.split('; ');
    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].split('=');
        if (cookie[0] === name) {
            return cookie[1];
        }
    }
    return null;
}

// Call the checkLoginStatus function and store the result in a variable
var isUserLoggedIn = checkLoginStatus();

// Use JavaScript to display the appropriate link based on the login status
var loginLink = document.getElementById("loginLink");
var logoutLink = document.getElementById("logoutLink");

if (isUserLoggedIn) {
    // User is logged in, show logout link
    logoutLink.style.display = "block";
} else {
    // User is not logged in, show login link
    loginLink.style.display = "block";
}

// Call the checkLoginStatus function when the page loads
window.onload = checkLoginStatus;
