require('dotenv').config();

const request = require('supertest');
const chai = require('chai');
const { expect } = chai;

const app = require('../server');       
const mongoose = require('mongoose');
const User = require('../models/user');
const bcrypt = require('bcrypt');

const ADMIN_USER = { 
  username: 'proUser',
  password: 'securePwd123'
};
const STANDARD_USER = {
  username: 'standardUser',
  password: 'userPwd'
};
const BAD_CREDENTIALS = { 
  username: 'invalid',
  password: 'user'
};

let adminToken = '';
let standardToken = '';

describe('JWT Authentication & Authorization Flow', function () {
  this.timeout(10000);

  before(async () => {
    try {
      const adminExists = await User.findOne({ username: ADMIN_USER.username });
      if (!adminExists) {
        await User.create({
          username: ADMIN_USER.username,
          password: ADMIN_USER.password, 
          role: 'admin'
        });
        console.log('Admin user created.');
      }

      const userExists = await User.findOne({ username: STANDARD_USER.username });
      if (!userExists) {
        await User.create({
          username: STANDARD_USER.username,
          password: STANDARD_USER.password, 
          role: 'user'
        });
        console.log('Standard user created.');
      }
    } catch (err) {
      console.error('ERROR', err);
      throw err;
    }
  });

  after(async () => {
    if (mongoose.connection.readyState !== 0) {
      await mongoose.connection.close();
      console.log('\n MongoDB connection closed.');
    }
  });

  describe('POST /api/auth/login', () => {
    it('successfully log in ADMIN user and store the token (200 OK)', async () => {
      const res = await request(app)
        .post('/api/auth/login')
        .send(ADMIN_USER);

      expect(res.status).to.equal(200);
      expect(res.body).to.have.property('token').that.is.a('string');
      adminToken = res.body.token;
    });

    it('successfully log in STANDARD user and store the token (200 OK)', async () => {
      const res = await request(app)
        .post('/api/auth/login')
        .send(STANDARD_USER);

      expect(res.status).to.equal(200);
      expect(res.body).to.have.property('token').that.is.a('string');
      standardToken = res.body.token;
    });

    it(' fail login with 401 for invalid credentials', async () => {
      const res = await request(app)
        .post('/api/auth/login')
        .send(BAD_CREDENTIALS);

      expect(res.status).to.equal(401);
      expect(res.body).to.have.property('message').equal('Authentication failed: Invalid credentials.');
    });
  });

  describe('GET /api/auth/protected/user-status', () => {
    it(' allow access to user-status with a valid ADMIN token (200 OK)', async () => {
      const res = await request(app)
        .get('/api/auth/protected/user-status')
        .set('Authorization', `Bearer ${adminToken}`);

      expect(res.status).to.equal(200);
      expect(res.body.data.verifiedClaims.role).to.equal('admin');
    });

    it(' allow access to user-status with a valid STANDARD user token (200 OK)', async () => {
      const res = await request(app)
        .get('/api/auth/protected/user-status')
        .set('Authorization', `Bearer ${standardToken}`);

      expect(res.status).to.equal(200);
      expect(res.body.data.verifiedClaims.role).to.equal('user');
    });

    it(' deny access with 401 when the Authorization header is MISSING', async () => {
      const res = await request(app)
        .get('/api/auth/protected/user-status');

      expect(res.status).to.equal(401);
      expect(res.body).to.have.property('message').equal('Unauthorized: Bearer token format required.');
    });

    it(' deny access with 403 for an INVALID/TAMPERED token', async () => {
      const tamperedToken = adminToken.slice(0, -2) + 'XX';

      const res = await request(app)
        .get('/api/auth/protected/user-status')
        .set('Authorization', `Bearer ${tamperedToken}`);

      expect(res.status).to.equal(403);
      expect(res.body).to.have.property('message').equal('Forbidden: Invalid or expired token.');
      expect(res.body).to.have.property('errorName').equal('JsonWebTokenError');
    });
  });
});
