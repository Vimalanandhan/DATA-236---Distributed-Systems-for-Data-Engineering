const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const cors = require('cors');
const ReActBikeShareAgent = require('./agent/react_agent');
const { convertCitiBikeCSV } = require('./utils/csv_converter');
const { createSampleFromLargeCSV } = require('./utils/sample_creator');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('ui'));

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const uploadDir = path.join(__dirname, 'uploads');
        if (!fs.existsSync(uploadDir)) {
            fs.mkdirSync(uploadDir, { recursive: true });
        }
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ 
    storage: storage,
    fileFilter: (req, file, cb) => {
        if (file.mimetype === 'text/csv' || path.extname(file.originalname).toLowerCase() === '.csv') {
            cb(null, true);
        } else {
            cb(new Error('Only CSV files are allowed'), false);
        }
    },
    limits: {
        fileSize: 50 * 1024 * 1024 // 50MB limit for large Citi Bike files
    }
});

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'ui', 'index.html'));
});

app.post('/api/analyze', upload.single('csvFile'), async (req, res) => {
    try {
        console.log('Received request:', {
            hasFile: !!req.file,
            fileName: req.file?.originalname,
            fileSize: req.file?.size,
            pricingUrl: req.body.pricingUrl,
            bodyKeys: Object.keys(req.body)
        });

        if (!req.file) {
            console.log('Error: No CSV file uploaded');
            return res.status(400).json({ error: 'No CSV file uploaded' });
        }

        if (!req.body.pricingUrl) {
            console.log('Error: Pricing URL is required');
            return res.status(400).json({ error: 'Pricing URL is required' });
        }

        // Validate URL
        try {
            new URL(req.body.pricingUrl);
        } catch (error) {
            console.log('Error: Invalid pricing URL:', req.body.pricingUrl);
            return res.status(400).json({ error: 'Invalid pricing URL' });
        }

        // Check file size and create sample if too large
        const fileSizeMB = req.file.size / (1024 * 1024);
        console.log(`File size: ${fileSizeMB.toFixed(2)} MB`);
        
        let processedPath = req.file.path;
        
        // If file is large (>5MB), create a sample first
        if (fileSizeMB > 5) {
            console.log('Large file detected, creating sample...');
            const samplePath = req.file.path.replace('.csv', '_sample.csv');
            const sampleResult = await createSampleFromLargeCSV(req.file.path, samplePath, 500);
            console.log('Sample created:', sampleResult);
            processedPath = samplePath;
        }
        
        // Convert CSV to our expected format
        const convertedPath = processedPath.replace('.csv', '_converted.csv');
        
        try {
            console.log('Converting CSV file...');
            const conversionResult = await convertCitiBikeCSV(processedPath, convertedPath, 500);
            console.log('Conversion result:', conversionResult);
            
            // Create agent and run analysis
            const agent = new ReActBikeShareAgent();
            
            try {
                const result = await agent.analyze(convertedPath, req.body.pricingUrl);
                
                // Clean up files
                fs.unlinkSync(req.file.path);
                if (processedPath !== req.file.path) {
                    fs.unlinkSync(processedPath); // Clean up sample file if created
                }
                fs.unlinkSync(convertedPath);
                
                // Clean up agent resources
                agent.cleanup();
                
                res.json(result);
                
            } catch (error) {
                // Clean up files on error
                if (fs.existsSync(req.file.path)) {
                    fs.unlinkSync(req.file.path);
                }
                if (processedPath !== req.file.path && fs.existsSync(processedPath)) {
                    fs.unlinkSync(processedPath);
                }
                if (fs.existsSync(convertedPath)) {
                    fs.unlinkSync(convertedPath);
                }
                
                // Clean up agent resources
                agent.cleanup();
                
                throw error;
            }
            
        } catch (conversionError) {
            console.error('CSV conversion error:', conversionError);
            
            // Clean up uploaded file
            if (fs.existsSync(req.file.path)) {
                fs.unlinkSync(req.file.path);
            }
            
            throw new Error(`Failed to process CSV file: ${conversionError.message}`);
        }

    } catch (error) {
        console.error('Analysis error:', error);
        res.status(500).json({ 
            error: 'Analysis failed', 
            message: error.message 
        });
    }
});

// Error handling middleware
app.use((error, req, res, next) => {
    if (error instanceof multer.MulterError) {
        if (error.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ error: 'File too large. Maximum size is 10MB.' });
        }
    }
    
    console.error('Server error:', error);
    res.status(500).json({ 
        error: 'Internal server error',
        message: error.message 
    });
});

// Start server
if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`Bike-Share Optimizer server running on port ${PORT}`);
        console.log(`Visit http://localhost:${PORT} to use the application`);
    });
}

module.exports = app;
