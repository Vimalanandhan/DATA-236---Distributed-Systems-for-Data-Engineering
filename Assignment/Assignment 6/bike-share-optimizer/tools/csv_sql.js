const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');

class CsvSqlTool {
    constructor() {
        this.db = null;
        this.sourceFile = null;
    }

    /**
     * Initialize the tool with uploaded CSV data
     * @param {string} csvFilePath - Path to the uploaded CSV file
     * @param {Array} headers - Array of column headers
     */
    async initialize(csvFilePath, headers) {
        return new Promise((resolve, reject) => {
            this.sourceFile = path.basename(csvFilePath);
            const dbPath = csvFilePath.replace('.csv', '.db');
            
            // Remove existing database if it exists
            if (fs.existsSync(dbPath)) {
                fs.unlinkSync(dbPath);
            }

            this.db = new sqlite3.Database(dbPath, (err) => {
                if (err) {
                    reject(err);
                    return;
                }
                resolve();
            });
        });
    }

    /**
     * Load CSV data into SQLite database
     * @param {string} csvFilePath - Path to the CSV file
     * @param {Array} headers - Array of column headers
     * @param {Array} rows - Array of data rows
     */
    async loadCsvData(csvFilePath, headers, rows) {
        return new Promise((resolve, reject) => {
            this.sourceFile = path.basename(csvFilePath);
            
            const createTableSQL = this.generateCreateTableSQL(headers);
            
            this.db.run(createTableSQL, (err) => {
                if (err) {
                    reject(err);
                    return;
                }

                const insertSQL = this.generateInsertSQL(headers);
                const stmt = this.db.prepare(insertSQL);
                
                let completed = 0;
                const total = rows.length;
                
                if (total === 0) {
                    stmt.finalize();
                    resolve();
                    return;
                }

                rows.forEach((row, index) => {
                    const paddedRow = [];
                    for (let i = 0; i < headers.length; i++) {
                        paddedRow.push(row[i] || '');
                    }
                    
                    stmt.run(paddedRow, (err) => {
                        if (err) {
                            console.error('Error inserting row:', err);
                            console.error('Row data:', paddedRow);
                            console.error('Headers:', headers);
                            reject(err);
                            return;
                        }
                        completed++;
                        if (completed === total) {
                            stmt.finalize();
                            resolve();
                        }
                    });
                });
            });
        });
    }

    /**
     * Generate CREATE TABLE SQL based on headers
     * @param {Array} headers - Array of column headers
     * @returns {string} SQL CREATE TABLE statement
     */
    generateCreateTableSQL(headers) {
        const columns = headers.map(header => {
            const cleanHeader = header.replace(/[^a-zA-Z0-9_]/g, '_');
            return `"${cleanHeader}" TEXT`;
        }).join(', ');
        
        return `CREATE TABLE trips (${columns})`;
    }

    /**
     * Generate INSERT SQL based on headers
     * @param {Array} headers - Array of column headers
     * @returns {string} SQL INSERT statement
     */
    generateInsertSQL(headers) {
        const columns = headers.map(header => {
            const cleanHeader = header.replace(/[^a-zA-Z0-9_]/g, '_');
            return `"${cleanHeader}"`;
        }).join(', ');
        
        const placeholders = headers.map(() => '?').join(', ');
        
        return `INSERT INTO trips (${columns}) VALUES (${placeholders})`;
    }

    /**
     * Execute SQL query
     * @param {string} sql - SQL query string
     * @returns {Object} Query result with success, data, error, source, ts
     */
    async execute(sql) {
        return new Promise((resolve) => {
            if (!this.db) {
                resolve({
                    success: false,
                    error: "Database not initialized. Please upload a CSV file first.",
                    source: this.sourceFile || "none",
                    ts: new Date().toISOString()
                });
                return;
            }

            const trimmedSql = sql.trim().toLowerCase();
            if (!trimmedSql.startsWith('select')) {
                resolve({
                    success: false,
                    error: "Only SELECT queries are allowed for security reasons",
                    source: this.sourceFile || "none",
                    ts: new Date().toISOString()
                });
                return;
            }

            this.db.all(sql, [], (err, rows) => {
                if (err) {
                    resolve({
                        success: false,
                        error: err.message,
                        source: this.sourceFile || "none",
                        ts: new Date().toISOString()
                    });
                    return;
                }

                resolve({
                    success: true,
                    data: {
                        rows: rows || [],
                        row_count: rows ? rows.length : 0,
                        source: this.sourceFile || "uploaded.csv"
                    },
                    source: this.sourceFile || "uploaded.csv",
                    ts: new Date().toISOString()
                });
            });
        });
    }

    close() {
        if (this.db) {
            this.db.close();
            this.db = null;
        }
    }
}

module.exports = CsvSqlTool;
