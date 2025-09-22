const express = require('express');
const router = express.Router();
const courses = require('../data/courses');
const isAuthenticated = require('../middleware/auth');

router.get('/dashboard', isAuthenticated, (req, res) => {
    res.render('dashboard', { 
        user: req.session.user,
        courses: courses
    });
});

module.exports = router;