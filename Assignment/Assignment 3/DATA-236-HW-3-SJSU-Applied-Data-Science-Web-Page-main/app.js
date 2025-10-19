const express = require('express');
const session = require('express-session');
const path = require('path');

// Import routes
const indexRouter = require('./routes/index');
const authRouter = require('./routes/auth');
const dashboardRouter = require('./routes/dashboard');

const app = express();
const port = 3000;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

app.use(session({
    secret: 'your_secret_key',
    resave: false,
    saveUninitialized: false,
    cookie: { 
        secure: process.env.NODE_ENV === 'production',
        httpOnly: true,
        maxAge: 1000 * 60 * 60 * 24
    },
    name: 'sessionId',
}));

// Use routes
app.use('/', indexRouter);
app.use('/', authRouter);
app.use('/', dashboardRouter);

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});