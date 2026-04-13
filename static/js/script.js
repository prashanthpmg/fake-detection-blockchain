document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Blockchain verification animation
    const verifyButtons = document.querySelectorAll('.verify-btn');
    verifyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const resultElement = this.nextElementSibling;
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Verifying...';
            
            // Simulate blockchain verification (in a real app, this would be an API call)
            setTimeout(() => {
                this.innerHTML = 'Verify';
                this.disabled = false;
                resultElement.classList.add('verified');
                resultElement.innerHTML = '<i class="bi bi-check-circle-fill"></i> Verified on Blockchain';
            }, 2000);
        });
    });
});