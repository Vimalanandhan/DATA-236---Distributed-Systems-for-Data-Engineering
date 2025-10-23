#!/usr/bin/env node

const fs = require('fs');
const csv = require('csv-parser');
const path = require('path');

/**
 * Create a manageable sample from large Citi Bike CSV files
 */
async function createSample(inputFile, outputFile = null, sampleSize = 500) {
    if (!outputFile) {
        const dir = path.dirname(inputFile);
        const name = path.basename(inputFile, '.csv');
        outputFile = path.join(dir, `${name}_sample_${sampleSize}.csv`);
    }
    
    console.log(`Creating sample of ${sampleSize} rows from ${inputFile}...`);
    console.log(`Output file: ${outputFile}`);
    
    return new Promise((resolve, reject) => {
        const trips = [];
        let totalRows = 0;
        let sampledRows = 0;
        
        fs.createReadStream(inputFile)
            .pipe(csv())
            .on('data', (row) => {
                totalRows++;
                
                // Sample every nth row to get a representative sample
                const sampleRate = Math.max(1, Math.floor(totalRows / sampleSize));
                if (totalRows % sampleRate === 0 && sampledRows < sampleSize) {
                    trips.push(row);
                    sampledRows++;
                }
            })
            .on('end', () => {
                if (trips.length === 0) {
                    reject(new Error('No data found in CSV file'));
                    return;
                }
                
                // Write sample CSV
                const headers = Object.keys(trips[0]);
                const csvContent = [headers.join(','), ...trips.map(trip => 
                    headers.map(header => trip[header] || '').join(',')
                )].join('\n');
                
                fs.writeFileSync(outputFile, csvContent);
                
                console.log(`✅ Created sample: ${trips.length} trips from ${totalRows} total rows`);
                console.log(`📁 Sample saved to: ${outputFile}`);
                console.log(`📊 Sample includes: ${headers.join(', ')}`);
                
                resolve({
                    inputFile,
                    outputFile,
                    sampleSize: trips.length,
                    totalRows,
                    headers
                });
            })
            .on('error', (error) => {
                reject(error);
            });
    });
}

// Command line usage
if (require.main === module) {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log('Usage: node create_sample.js <input_csv> [output_csv] [sample_size]');
        console.log('');
        console.log('Examples:');
        console.log('  node create_sample.js 202301-citibike-tripdata_1.csv');
        console.log('  node create_sample.js 202301-citibike-tripdata_1.csv sample.csv 1000');
        process.exit(1);
    }
    
    const inputFile = args[0];
    const outputFile = args[1] || null;
    const sampleSize = parseInt(args[2]) || 500;
    
    if (!fs.existsSync(inputFile)) {
        console.error(`❌ File not found: ${inputFile}`);
        process.exit(1);
    }
    
    createSample(inputFile, outputFile, sampleSize)
        .then(result => {
            console.log('🎉 Sample creation completed successfully!');
            console.log(`📈 You can now upload ${result.outputFile} to the Bike-Share Optimizer`);
        })
        .catch(error => {
            console.error('❌ Error creating sample:', error.message);
            process.exit(1);
        });
}

module.exports = { createSample };
