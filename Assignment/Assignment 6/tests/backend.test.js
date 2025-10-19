const assert = require('assert');
const mongoose = require('mongoose');
const request = require('supertest');
const express = require('express');
const bodyParser = require('body-parser');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

const User = require('../models/user');
const app = require('../server'); // Assuming server.js exports the express app

describe('Backend Tests', () => {
    let testUser;
    let server;

    before(async () => {
        // Start the server
        server = app.listen(3001, () => {
            console.log('Test server running on port 3001');
            app.address = () => ({ port: 3001 });
        });

        // Create a test user
        testUser = new User({
            username: 'testuser',
            email: 'test@example.com',
            password: 'password123',
        });
        await testUser.save();
    });

    after(async () => {
        // Clean up the database after tests
        await mongoose.connection.db.dropDatabase();
        await mongoose.disconnect();
        await server.close();
    });

    it('should register a new user', async () => {
        const response = await request(app)
            .post('/api/auth/register')
            .send({
                username: 'newuser',
                email: 'new@example.com',
                password: 'password123',
            });

        assert.strictEqual(response.status, 201);
        assert.strictEqual(response.body.message, 'User created successfully');
        assert.ok(response.header.authorization); // Check if JWT token is in header
    });
});
