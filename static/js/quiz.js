/**
 * Quiz functionality for the Quiz Platform
 */

// Global variable to track the timer
let quizTimer;
let timeLeft;
let timerElement;

/**
 * Initialize the quiz timer
 * @param {number} duration - Quiz duration in minutes
 */
function initQuizTimer(duration) {
    timerElement = document.getElementById('timer');
    if (!timerElement) return;
    
    // Convert minutes to seconds
    timeLeft = duration * 60;
    
    // Update the timer immediately and then every second
    updateTimer();
    quizTimer = setInterval(updateTimer, 1000);
}

/**
 * Update the timer display
 */
function updateTimer() {
    if (timeLeft <= 0) {
        clearInterval(quizTimer);
        // Automatically submit the quiz when time runs out
        document.getElementById('quiz-form').submit();
        return;
    }
    
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    
    // Format the time as MM:SS
    timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    
    // Apply warning class when less than 1 minute remains
    if (timeLeft <= 60) {
        timerElement.classList.add('text-danger');
    }
    
    timeLeft--;
}

/**
 * Confirm quiz submission
 * @returns {boolean} True if confirmed, false otherwise
 */
function confirmSubmit() {
    const unansweredCount = document.querySelectorAll('.question-container:not(.answered)').length;
    
    if (unansweredCount > 0) {
        return confirm(`You have ${unansweredCount} unanswered question(s). Are you sure you want to submit?`);
    }
    
    return confirm('Are you sure you want to submit your quiz?');
}

/**
 * Mark a question as answered
 * @param {string} questionId - The ID of the question
 */
function markAsAnswered(questionId) {
    const questionContainer = document.getElementById(`question-${questionId}`);
    if (questionContainer) {
        questionContainer.classList.add('answered');
    }
}

/**
 * Initialize the quiz functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get the quiz duration from the data attribute
    const quizContainer = document.getElementById('quiz-container');
    if (quizContainer) {
        const duration = quizContainer.dataset.duration;
        if (duration) {
            initQuizTimer(parseInt(duration));
        }
    }
    
    // Add event listeners to all radio buttons
    const radioButtons = document.querySelectorAll('input[type="radio"]');
    radioButtons.forEach(function(radio) {
        radio.addEventListener('change', function() {
            const questionId = this.name.split('_')[1];
            markAsAnswered(questionId);
        });
    });
    
    // Add submit confirmation
    const quizForm = document.getElementById('quiz-form');
    if (quizForm) {
        quizForm.addEventListener('submit', function(event) {
            if (!confirmSubmit()) {
                event.preventDefault();
            }
        });
    }
});
