// Form handling and user feedback
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('topicForm');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            const input = form.querySelector('.topic-input');
            
            // Validate input
            if (!input.value.trim()) {
                e.preventDefault();
                showError('Please enter a topic');
                return;
            }
            
            if (input.value.trim().length < 3) {
                e.preventDefault();
                showError('Topic must be at least 3 characters long');
                return;
            }
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <svg class="btn-icon spinning" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                </svg>
                Generating...
            `;
        });
    }
});

function showError(message) {
    // Remove existing error messages
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `<p>${message}</p>`;
    
    // Insert before form
    const form = document.getElementById('topicForm');
    form.parentNode.insertBefore(errorDiv, form);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Add spinning animation for loading state
const style = document.createElement('style');
style.textContent = `
    .spinning {
        animation: spin 1s linear infinite;
    }
`;
document.head.appendChild(style);
