/* Custom JavaScript for pyhfm documentation */

// Add copy to clipboard functionality for code blocks
document.addEventListener('DOMContentLoaded', function() {
    // Add copy buttons to code blocks that don't already have them
    const codeBlocks = document.querySelectorAll('pre code');

    codeBlocks.forEach(function(block) {
        const pre = block.parentElement;
        if (!pre.querySelector('.md-clipboard')) {
            const button = document.createElement('button');
            button.className = 'md-clipboard md-icon';
            button.title = 'Copy to clipboard';
            button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"></path></svg>';

            button.addEventListener('click', function() {
                navigator.clipboard.writeText(block.textContent).then(function() {
                    button.classList.add('md-clipboard--success');
                    setTimeout(function() {
                        button.classList.remove('md-clipboard--success');
                    }, 2000);
                });
            });

            pre.appendChild(button);
        }
    });
});

// Add smooth scrolling for anchor links
document.addEventListener('click', function(e) {
    if (e.target.matches('a[href^="#"]')) {
        e.preventDefault();
        const target = document.querySelector(e.target.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
});
