require('dotenv').config();
const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const User = require('../models/user');
const verifyToken = require('../middleware/auth'); // Import isolated middleware

const router = express.Router();

// ----------------------------------------------------------------------
// --- 1. Registration (Endpoint to create new users) ---
// ----------------------------------------------------------------------

router.post('/register', async (req, res) => {
    const { username, password, role } = req.body;

    // Basic input validation
    if (!username || !password) {
        return res.status(400).json({ message: "Username and password are required." });
    }

    try {
        // Check if user already exists
        let user = await User.findOne({ username });
        if (user) {
            return res.status(409).json({ message: "User already exists." }); // 409 Conflict
        }

        // HASH THE PASSWORD before saving (Best Practice!)
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(password, salt);

        user = new User({ 
            username, 
            password: hashedPassword,
            role: role || 'user' // Default role to 'user' if not provided
        });

        await user.save();

        // Respond with success (do not return password)
        res.status(201).json({ 
            message: "User registered successfully.", 
            username: user.username, 
            role: user.role 
        }); // 201 Created

    } catch (error) {
        console.error(error.message);
        res.status(500).json({ message: "Server error during registration." });
    }
});

// ----------------------------------------------------------------------
// --- 2. Login (Token Generation) ---
// ----------------------------------------------------------------------

router.post('/login', async (req, res) => {
    const { username, password } = req.body;

    try {
        // 1. Find user in MongoDB
        const user = await User.findOne({ username });

        if (!user) {
            return res.status(401).json({ message: "Authentication failed: Invalid credentials." });
        }
        
        // 2. COMPARE HASHED PASSWORD (Best Practice!)
        const isMatch = await bcrypt.compare(password, user.password);

        if (!isMatch) {
            return res.status(401).json({ message: "Authentication failed: Invalid credentials." });
        }
        
        // 3. Define the payload (claims)
        const payload = {
            id: user._id, 
            username: user.username,
            role: user.role
        };
        
        // 4. Create and sign the JWT
        jwt.sign(
            payload, 
            process.env.JWT_SECRET, 
            { expiresIn: process.env.TOKEN_EXPIRY || '24h' }, 
            (err, token) => {
                if (err) throw err;
                
                // 5. Send the token back
                res.json({
                    message: "Login successful.",
                    token: token,
                    expiresIn: process.env.TOKEN_EXPIRY || '24h'
                });
            }
        );

    } catch (error) {
        console.error(error.message);
        res.status(500).json({ message: "Server error during login." });
    }
});

router.get('/protected/user-status', verifyToken, (req, res) => {
    
    if (req.user.role !== 'admin' && req.user.role !== 'user') {
        return res.status(403).json({ 
            message: "Access Denied: Requires 'admin' or 'user' role.", 
            userRole: req.user.role 
        });
    }

    res.json({
        message: "SUCCESS! You accessed the protected user resource.",
        data: {
            sensitiveInfo: `Welcome, ${req.user.username}. You are authorized as '${req.user.role}'.`,
            verifiedClaims: req.user
        }
    });
});

module.exports = router;
