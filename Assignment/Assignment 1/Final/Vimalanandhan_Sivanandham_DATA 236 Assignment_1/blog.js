// Blog Application JavaScript

// 1. Arrow function to validate blog content length and terms checkbox
const validateBlogForm = () => {
    const blogContent = document.getElementById('blogContent').value;
    const termsChecked = document.getElementById('termsConditions').checked;
    
    // Validate blog content length (more than 25 characters)
    if (blogContent.length <= 25) {
        alert('Blog content should be more than 25 characters');
        return false;
    }
    
    // Validate terms and conditions checkbox
    if (!termsChecked) {
        alert('You must agree to the terms and conditions');
        return false;
    }
    
    return true;
};

// 2. Closure to track form submission count
const submissionCounter = (() => {
    let count = 0;
    return () => {
        count++;
        return count;
    };
})();

// 3. Form submission handler
document.getElementById('blogForm').addEventListener('submit', (e) => {
    e.preventDefault();
    
    // Validate form using arrow function
    if (!validateBlogForm()) {
        return;
    }
    
    // Collect form data
    const formData = {
        title: document.getElementById('blogTitle').value,
        author: document.getElementById('authorName').value,
        email: document.getElementById('emailAddress').value,
        content: document.getElementById('blogContent').value,
        category: document.getElementById('category').value,
        termsAccepted: document.getElementById('termsConditions').checked
    };
    
    // Convert form data to JSON string and log to console
    const jsonData = JSON.stringify(formData, null, 2);
    console.log('Form Data (JSON):', jsonData);
    
    // Parse JSON back to object
    const parsedData = JSON.parse(jsonData);
    console.log('Parsed Data:', parsedData);
    
    // 4. Use object destructuring to extract title and email
    const { title, email } = parsedData;
    console.log('Extracted Title:', title);
    console.log('Extracted Email:', email);
    
    // 5. Use spread operator to add submissionDate
    const updatedData = { 
        ...parsedData, 
        submissionDate: new Date().toISOString() 
    };
    console.log('Updated Data with Submission Date:', updatedData);
    
    // 6. Use closure to track submission count
    const submissionCount = submissionCounter();
    console.log(`Form has been successfully submitted ${submissionCount} time(s)`);
    
    // Show success message
    alert(`Blog published successfully! This is submission #${submissionCount}`);
    
    // Reset form
    document.getElementById('blogForm').reset();
    
    // Refocus on the first field
    document.getElementById('blogTitle').focus();
});
