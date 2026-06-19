/**
 * Verification Code Auto-Jump
 */
document.addEventListener('DOMContentLoaded', () => {
    const inputs = document.querySelectorAll('.code-input');
    
    inputs.forEach((input, index) => {
        input.addEventListener('input', (e) => {
            if (e.target.value.length === 1) {
                if (index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
            }
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && e.target.value.length === 0) {
                if (index > 0) {
                    inputs[index - 1].focus();
                }
            }
        });
        
        // Paste support
        input.addEventListener('paste', (e) => {
            e.preventDefault();
            const data = e.clipboardData.getData('text');
            if (data.length === 6 && /^\d+$/.test(data)) {
                inputs.forEach((inp, i) => {
                    inp.value = data[i];
                });
                inputs[inputs.length - 1].focus();
            }
        });
    });
});
