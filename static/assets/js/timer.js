// select the HTML element that will display the countdown timer
const countdownElement = document.getElementById("countdown");

// set the initial time for the countdown (in seconds)
let timeRemaining = 15;

// update the countdown element every second
const countdownInterval = setInterval(() => {
  // decrement the time remaining
  timeRemaining -= 1;

  // format the time remaining as "mm:ss"
  const minutes = Math.floor(timeRemaining / 60).toString().padStart(2, "0");
  const seconds = (timeRemaining % 60).toString().padStart(2, "0");
  const formattedTime = `${minutes}:${seconds}`;

  // update the countdown element with the formatted time
  countdownElement.textContent = formattedTime;

  // if the countdown has reached zero, submit the form and stop the interval
  if (timeRemaining <= 0) {
    
 clearInterval(countdownInterval);
    const formElement = document.getElementById("session");
    formElement.submit();
  }
}, 1000);
