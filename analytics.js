/**
 * Vercel Web Analytics initialization
 * Loads the analytics tracking for this site
 */
(function() {
  'use strict';
  
  // Initialize Vercel Analytics queue
  window.va = window.va || function () { 
    (window.vaq = window.vaq || []).push(arguments); 
  };
  
  // Load the analytics script
  var script = document.createElement('script');
  script.defer = true;
  script.src = '/_vercel/insights/script.js';
  
  // Append to head
  if (document.head) {
    document.head.appendChild(script);
  }
})();
