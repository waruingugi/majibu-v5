// Get the current date and time
const now = new Date();

// Calculate the remaining time until tomorrow at 8:00 AM in Nairobi
const tomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 9, 0, 0, 0);
const remainingTime = tomorrow - now;

// Update the data-date attribute with the new date
const countdownTimer = document.querySelector('.countdown-timer');
countdownTimer.setAttribute('data-date', tomorrow.toISOString());

// Start the countdown timer
$(countdownTimer).TimeCircles();
