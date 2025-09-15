const express = require('express');
const app = express();
const bodyParser = require('body-parser');

app.set('view engine', 'ejs');
app.set('views', './views');
app.use(express.static(__dirname + '/public'));

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

let books = [
    { "BookID": "1", "Title": "Book 1", "Author": "Author 1" },
    { "BookID": "2", "Title": "Book 2", "Author": "Author 2" },
    { "BookID": "3", "Title": "Book 3", "Author": "Author 3" }
];

app.get('/', function (req, res) {
    res.render('home', {
        books: books
    });
});

// Add Book
app.get('/add-book', function (req, res) {
    res.render('create');
});

app.post('/add-book', function (req, res) {
    const newBook = {
        "BookID": (books.length + 1).toString(),
        "Title": req.body.title,
        "Author": req.body.author
    };
    books.push(newBook);
    res.redirect('/');
});


app.get('/update-book', function (req, res) {
    res.render('update-book', { book: null });
});

app.post('/update-book', function (req, res) {
    const bookIdToUpdate = String(req.body.bookId);

    const bookToUpdate = books.find(book => book.BookID === bookIdToUpdate);
    if (!bookToUpdate) {
        return res.send("Book not found");
    }

    const updatedBook = {
        "BookID": bookIdToUpdate,
        "Title": req.body.title,
        "Author": req.body.author
    };

    books = books.map(book =>
        book.BookID === bookIdToUpdate ? updatedBook : book
    );

    res.redirect('/');
});

app.get('/delete-book', function (req, res) {
    res.render('delete');
});

app.post('/delete-book', function (req, res) {
    const bookIdToDelete = req.body.bookId;

    if (!bookIdToDelete) {
        return res.send("Book ID is required");
    }

    books = books.filter(book => book.BookID !== bookIdToDelete);

    res.redirect('/');
});



app.listen(5001, function () {
    console.log("Server listening on port 5001");
});