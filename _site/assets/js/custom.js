document.addEventListener('DOMContentLoaded', function() {
  // Initialize theme based on localStorage or default to dark mode
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'light') {
    document.body.classList.remove('dark');
    document.documentElement.setAttribute('data-theme', 'light');
  } else {
    document.body.classList.add('dark');
    document.documentElement.setAttribute('data-theme', 'dark');
  }
  
  // Set the correct state of the theme toggle checkbox
  const themeToggleCheckbox = document.getElementById('theme-toggle');
  if (themeToggleCheckbox) {
    themeToggleCheckbox.checked = savedTheme !== 'light';
  }
  
  // Handle mobile menu toggle
  const mobileMenuToggle = document.querySelector('[onclick="toggleNavbar(\'navbar\')"]');
  if (mobileMenuToggle) {
    // Redirect the onclick to our custom function
    mobileMenuToggle.setAttribute('onclick', 'toggleMobileMenu()');
  }
  
  // Add copy buttons to all code blocks
  addCopyButtonsToCodeBlocks();
});

// Theme toggle function
function themeToggle() {
  const isDark = document.body.classList.contains('dark');
  if (isDark) {
    document.body.classList.remove('dark');
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem('theme', 'light');
  } else {
    document.body.classList.add('dark');
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
  }
}

// Mobile menu toggle function
function toggleMobileMenu() {
  const navbar = document.getElementById('navbar');
  if (navbar) {
    navbar.classList.toggle('hidden');
  }
}

// Check if we're on mobile
function isMobile() {
  return window.innerWidth <= 768;
}

// Disable video on mobile
function handleVideoPlayback() {
  const video = document.querySelector('.background-video');
  if (video) {
    if (isMobile()) {
      video.pause();
    } else {
      video.play();
    }
  }
}

// Add copy buttons and language badges to code blocks
function addCopyButtonsToCodeBlocks() {
  // Find all <pre> elements (code blocks)
  const codeBlocks = document.querySelectorAll('pre');
  
  codeBlocks.forEach(codeBlock => {
    // Create the copy button
    const copyButton = document.createElement('button');
    copyButton.className = 'copy-button';
    copyButton.textContent = 'Copy';
    
    // Add the button to the code block
    codeBlock.appendChild(copyButton);
    
    // Add language badge if available
    const codeElement = codeBlock.querySelector('code');
    if (codeElement) {
      // Extract language from class if available (e.g., "language-javascript")
      const classes = codeElement.className.split(' ');
      const langClass = classes.find(cls => cls.startsWith('language-'));
      
      if (langClass) {
        const language = langClass.replace('language-', '');
        // Set data-lang attribute for the ::before pseudo-element in CSS
        codeBlock.setAttribute('data-lang', language);
      } else {
        // Default to "code" if no language specified
        codeBlock.setAttribute('data-lang', 'code');
      }
    }
    
    // Add click event to copy the code content
    copyButton.addEventListener('click', function() {
      // Get the code content excluding the button itself
      const codeElement = codeBlock.querySelector('code') || codeBlock;
      let codeText = codeElement.textContent;
      
      // Copy to clipboard
      navigator.clipboard.writeText(codeText).then(() => {
        // Change the button text to indicate success
        copyButton.textContent = 'Copied!';
        copyButton.classList.add('copied');
        
        // Reset the button after 2 seconds
        setTimeout(() => {
          copyButton.textContent = 'Copy';
          copyButton.classList.remove('copied');
        }, 2000);
      }).catch(err => {
        console.error('Failed to copy text: ', err);
        copyButton.textContent = 'Failed!';
        
        // Reset the button after 2 seconds
        setTimeout(() => {
          copyButton.textContent = 'Copy';
        }, 2000);
      });
    });
  });
}

// Run on load and on resize
window.addEventListener('load', handleVideoPlayback);
window.addEventListener('resize', handleVideoPlayback);

// Re-add copy buttons when content changes (e.g., navigation)
document.addEventListener('DOMContentLoaded', function() {
  // Add mutation observer to detect new code blocks
  const observer = new MutationObserver(mutations => {
    mutations.forEach(mutation => {
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        // Check if we need to add new copy buttons
        const codeBlocks = document.querySelectorAll('pre:not(:has(.copy-button))');
        if (codeBlocks.length > 0) {
          addCopyButtonsToCodeBlocks();
        }
      }
    });
  });
  
  // Start observing the document for added code blocks
  observer.observe(document.body, { childList: true, subtree: true });
});
