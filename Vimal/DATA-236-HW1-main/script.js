const myField1 = document.getElementById("title");
myField1.focus();

const blogForm = document.getElementById('blogForm');
const blogDisplay = document.getElementById('blogDisplay');

const submissionCounter = (() => {
    let count = 0;
    return () => {
        count++;
        console.log(`Form submitted ${count} time(s).`);
        return count;
    };
})();

const validateForm = (event) => {
    event.preventDefault();

    const contentText = document.getElementById('content').value; // Renamed to contentText

    const terms = document.getElementById('terms').checked;

    if (contentText.length <= 25) { // Use contentText here
        alert("Blog content should be more than 25 characters");
        return;
    }

    if (!terms) {
        alert("You must agree to the terms and conditions");
        return;
    }

    const formData = new FormData(blogForm);
    const formDataObject = Object.fromEntries(formData.entries());
    const jsonData = JSON.stringify(formDataObject);

    console.log("JSON Data:", jsonData);

    const parsedObject = JSON.parse(jsonData);

    const { title, author, email, category } = parsedObject;  // Destructure, but *omit* content here

    console.log("Title:", title);
    console.log("Author:", author);
    console.log("Email:", email);
    console.log("Category:", category);
    console.log("Content:", contentText);

    const updatedObject = { ...parsedObject, content: contentText, submissionDate: new Date().toISOString() };
    console.log("Updated Object:", updatedObject);

    const currentCount = submissionCounter();
    displayBlog(updatedObject, currentCount);

    blogForm.reset();
};

const displayBlog = (blogData, count) => {
    const blogEntry = document.createElement('div');
    blogEntry.classList.add('blog-entry');

    blogEntry.innerHTML = `
        <h2>${blogData.title}</h2>
        <p><strong>Author:</strong> ${blogData.author}</p>
        <p><strong>Email:</strong> ${blogData.email}</p>
        <p><strong>Category:</strong> ${blogData.category}</p>
        <p>${blogData.content}</p>
        <p><strong>Submission Date:</strong> ${new Date(blogData.submissionDate).toLocaleString()}</p>
        <p><strong>Submission Count:</strong> ${count}</p>
    `;
    blogDisplay.appendChild(blogEntry);
};

blogForm.addEventListener('submit', validateForm);