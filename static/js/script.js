async function explainCode() {
    const codeInput = document.getElementById('codeInput');
    const languageSelect = document.getElementById('language');
    const explanationOutput = document.getElementById('explanationOutput');
    const loadingElement = document.getElementById('loading');
    const explainBtn = document.getElementById('explainBtn');

    const code = codeInput.value.trim();

    if (!code) {
        alert('Please paste some code first!');
        return;
    }

    // Show loading state
    explainBtn.disabled = true;
    explainBtn.textContent = 'Analyzing...';
    explanationOutput.classList.add('hidden');
    loadingElement.classList.remove('hidden');

    try {
        const response = await fetch('/api/explain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code: code,
                language: languageSelect.value
            })
        });

        const data = await response.json();

        if (data.success) {
            explanationOutput.innerHTML = `
                <div class="explanation-content">${data.explanation}</div>
            `;
        } else {
            explanationOutput.innerHTML = `
                <div class="error">Error: ${data.detail || 'Unknown error occurred'}</div>
            `;
        }

    } catch (error) {
        console.error('Error:', error);
        explanationOutput.innerHTML = `
            <div class="error">Network error: Could not connect to the server</div>
        `;
    } finally {
        // Hide loading state
        loadingElement.classList.add('hidden');
        explanationOutput.classList.remove('hidden');
        explainBtn.disabled = false;
        explainBtn.textContent = 'Explain Code';
    }
}

// Add event listener for Enter key with Ctrl/Cmd
document.getElementById('codeInput').addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        explainCode();
    }
});

// Auto-resize textarea
document.getElementById('codeInput').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});