const CsvSqlTool = require('../tools/csv_sql');
const PolicyRetrieverTool = require('../tools/policy_retriever');
const CalculatorTool = require('../tools/calculator');
const fs = require('fs');
const csv = require('csv-parser');


class ReActBikeShareAgent {
    constructor() {
        this.csvTool = new CsvSqlTool();
        this.policyTool = new PolicyRetrieverTool();
        this.calculatorTool = new CalculatorTool();
        
        this.steps = [];
        this.startTime = null;
        this.stopReason = null;
    }

    /**
     * Main entry point for the agent
     * @param {string} csvFilePath - Path to the uploaded CSV file
     * @param {string} pricingUrl - URL to the pricing policy page
     * @returns {Object} Analysis result with decision and justification
     */
    async analyze(csvFilePath, pricingUrl) {
        this.startTime = Date.now();
        this.steps = [];
        
        try {
            await this.addStep('Thought', 'Loading and analyzing trip data from CSV file...');
            const tripAnalysis = await this.analyzeTripData(csvFilePath);
            
            await this.addStep('Thought', 'Retrieving pricing policy information...');
            const pricingInfo = await this.retrievePricingPolicy(pricingUrl);
            
            await this.addStep('Thought', 'Calculating costs for both pay-per-use and membership options...');
            const costAnalysis = await this.calculateCosts(tripAnalysis, pricingInfo);
            
            await this.addStep('Thought', 'Analyzing cost comparison to make final recommendation...');
            const decision = this.makeDecision(costAnalysis);
            
            await this.addStep('Final Answer', this.generateFinalAnswer(decision, costAnalysis, pricingInfo));
            
            this.stopReason = 'completed';
            
            return {
                decision: decision.recommendation,
                justification: decision.justification,
                costBreakdown: costAnalysis,
                citations: pricingInfo.citations,
                steps: this.steps,
                totalSteps: this.steps.length,
                totalTime: Date.now() - this.startTime,
                stopReason: this.stopReason
            };
            
        } catch (error) {
            this.stopReason = 'error';
            await this.addStep('Error', `Analysis failed: ${error.message}`);
            
            return {
                decision: 'Unable to determine',
                justification: `Analysis failed due to error: ${error.message}`,
                costBreakdown: null,
                citations: [],
                steps: this.steps,
                totalSteps: this.steps.length,
                totalTime: Date.now() - this.startTime,
                stopReason: this.stopReason
            };
        }
    }

    /**
     * Analyze trip data from CSV
     * @param {string} csvFilePath - Path to CSV file
     * @returns {Object} Trip analysis results
     */
    async analyzeTripData(csvFilePath) {
        const trips = await this.loadCsvData(csvFilePath);
        
        if (trips.length === 0) {
            throw new Error('No trip data found in CSV file');
        }
        
        const headers = Object.keys(trips[0]);
        console.log('CSV Headers:', headers);
        
        await this.csvTool.initialize(csvFilePath, headers);
        await this.csvTool.loadCsvData(csvFilePath, headers, trips);
        
        const analysis = await this.performTripAnalysis();
        
        await this.addStep('Action', 'csv_sql', {
            sql: 'SELECT COUNT(*) as total_trips, AVG(CAST(duration AS REAL)) as avg_duration FROM trips'
        });
        
        return analysis;
    }

    /**
     * Load CSV data into memory
     * @param {string} csvFilePath - Path to CSV file
     * @returns {Array} Array of trip objects
     */
    async loadCsvData(csvFilePath) {
        return new Promise((resolve, reject) => {
            const trips = [];
            const headers = [];
            let isFirstRow = true;
            
            fs.createReadStream(csvFilePath)
                .pipe(csv())
                .on('data', (row) => {
                    if (isFirstRow) {
                        headers.push(...Object.keys(row));
                        isFirstRow = false;
                        console.log('CSV Headers detected:', headers);
                    }
                    trips.push(row);
                })
                .on('end', () => {
                    console.log('Loaded CSV data:', {
                        rowCount: trips.length,
                        headers: headers,
                        sampleRow: trips[0]
                    });
                    
                    if (trips.length === 0) {
                        reject(new Error('No data found in CSV file'));
                        return;
                    }
                    
                    resolve(trips);
                })
                .on('error', (error) => {
                    console.error('CSV loading error:', error);
                    reject(new Error(`Failed to parse CSV file: ${error.message}`));
                });
        });
    }

    /**
     * Perform comprehensive trip analysis
     * @returns {Object} Analysis results
     */
    async performTripAnalysis() {
        const basicStats = await this.csvTool.execute(`
            SELECT 
                COUNT(*) as total_trips,
                AVG(CAST(duration AS REAL)) as avg_duration,
                SUM(CAST(duration AS REAL)) as total_duration,
                COUNT(CASE WHEN bike_type = 'ebike' OR bike_type = 'electric' THEN 1 END) as ebike_trips,
                COUNT(CASE WHEN bike_type = 'classic' OR bike_type = 'docked' THEN 1 END) as classic_trips
            FROM trips
        `);

        const weeklyStats = await this.csvTool.execute(`
            SELECT 
                strftime('%W', start_time) as week,
                COUNT(*) as trip_count,
                AVG(CAST(duration AS REAL)) as avg_duration,
                COUNT(CASE WHEN bike_type = 'ebike' OR bike_type = 'electric' THEN 1 END) as ebike_count
            FROM trips 
            GROUP BY strftime('%W', start_time)
            ORDER BY week
        `);

        const durationStats = await this.csvTool.execute(`
            SELECT 
                CASE 
                    WHEN CAST(duration AS REAL) <= 15 THEN '0-15 min'
                    WHEN CAST(duration AS REAL) <= 30 THEN '15-30 min'
                    WHEN CAST(duration AS REAL) <= 60 THEN '30-60 min'
                    ELSE '60+ min'
                END as duration_range,
                COUNT(*) as count
            FROM trips
            GROUP BY duration_range
        `);

        await this.addStep('Observation', `Found ${basicStats.data.rows[0].total_trips} total trips with average duration of ${Math.round(basicStats.data.rows[0].avg_duration)} minutes`);

        return {
            totalTrips: basicStats.data.rows[0].total_trips,
            avgDuration: basicStats.data.rows[0].avg_duration,
            totalDuration: basicStats.data.rows[0].total_duration,
            ebikeTrips: basicStats.data.rows[0].ebike_trips,
            classicTrips: basicStats.data.rows[0].classic_trips,
            weeklyBreakdown: weeklyStats.data.rows,
            durationDistribution: durationStats.data.rows
        };
    }

    /**
     * Retrieve pricing policy information
     * @param {string} pricingUrl - URL to pricing page
     * @returns {Object} Pricing information
     */
    async retrievePricingPolicy(pricingUrl) {
        const queries = [
            'membership price monthly annual',
            'per ride cost minute charge',
            'unlock fee',
            'ebike surcharge electric bike',
            'overage fee additional charge',
            'included minutes membership'
        ];

        const allPassages = [];
        
        for (const query of queries) {
            await this.addStep('Action', 'policy_retriever', {
                url: pricingUrl,
                query: query,
                k: 3
            });
            
            const result = await this.policyTool.retrieve(pricingUrl, query, 3);
            
            if (result.success) {
                allPassages.push(...result.data.passages);
                await this.addStep('Observation', `Retrieved ${result.data.passages.length} relevant passages for query: ${query}`);
            } else {
                await this.addStep('Observation', `Failed to retrieve policy for query: ${query} - ${result.error}`);
            }
        }

        const pricingInfo = this.extractPricingInfo(allPassages);
        
        return {
            passages: allPassages,
            pricing: pricingInfo,
            citations: [{
                url: pricingUrl,
                date: new Date().toISOString(),
                passages: allPassages.slice(0, 10) 
            }]
        };
    }

    /**
     * Extract structured pricing information from passages
     * @param {Array} passages - Array of policy passages
     * @returns {Object} Structured pricing information
     */
    extractPricingInfo(passages) {
        const pricing = {
            membershipPrice: null,
            perRideCost: null,
            perMinuteCost: null,
            unlockFee: null,
            ebikeSurcharge: null,
            includedMinutes: null,
            overageFee: null
        };

        passages.forEach(passage => {
            const text = passage.text.toLowerCase();
            
            if (text.includes('membership') && text.includes('$')) {
                const priceMatch = text.match(/\$(\d+(?:\.\d{2})?)/);
                if (priceMatch && !pricing.membershipPrice) {
                    pricing.membershipPrice = parseFloat(priceMatch[1]);
                }
            }
            
            if (text.includes('per ride') && text.includes('$')) {
                const priceMatch = text.match(/\$(\d+(?:\.\d{2})?)/);
                if (priceMatch && !pricing.perRideCost) {
                    pricing.perRideCost = parseFloat(priceMatch[1]);
                }
            }
            
            if (text.includes('per minute') && text.includes('$')) {
                const priceMatch = text.match(/\$(\d+(?:\.\d{2})?)/);
                if (priceMatch && !pricing.perMinuteCost) {
                    pricing.perMinuteCost = parseFloat(priceMatch[1]);
                }
            }
            
            if (text.includes('unlock') && text.includes('$')) {
                const priceMatch = text.match(/\$(\d+(?:\.\d{2})?)/);
                if (priceMatch && !pricing.unlockFee) {
                    pricing.unlockFee = parseFloat(priceMatch[1]);
                }
            }
            
            if ((text.includes('ebike') || text.includes('electric')) && text.includes('$')) {
                const priceMatch = text.match(/\$(\d+(?:\.\d{2})?)/);
                if (priceMatch && !pricing.ebikeSurcharge) {
                    pricing.ebikeSurcharge = parseFloat(priceMatch[1]);
                }
            }
        });

        return pricing;
    }

    /**
     * Calculate costs for both options
     * @param {Object} tripAnalysis - Trip analysis results
     * @param {Object} pricingInfo - Pricing information
     * @returns {Object} Cost analysis
     */
    async calculateCosts(tripAnalysis, pricingInfo) {
        const pricing = pricingInfo.pricing;
        
        const payPerUseCost = await this.calculatePayPerUseCost(tripAnalysis, pricing);
        
        const membershipCost = await this.calculateMembershipCost(tripAnalysis, pricing);
        
        const breakEvenAnalysis = await this.calculateBreakEven(tripAnalysis, pricing);
        
        return {
            payPerUse: payPerUseCost,
            membership: membershipCost,
            breakEven: breakEvenAnalysis,
            savings: membershipCost.total - payPerUseCost.total
        };
    }

    /**
     * Calculate pay-per-use costs
     * @param {Object} tripAnalysis - Trip analysis
     * @param {Object} pricing - Pricing information
     * @returns {Object} Pay-per-use cost breakdown
     */
    async calculatePayPerUseCost(tripAnalysis, pricing) {
        const totalTrips = tripAnalysis.totalTrips;
        const avgDuration = tripAnalysis.avgDuration;
        const ebikeTrips = tripAnalysis.ebikeTrips;
        const classicTrips = tripAnalysis.classicTrips;
        
        const unlockFee = pricing.unlockFee || 1.00;
        const perMinuteCost = pricing.perMinuteCost || 0.15;
        const ebikeSurcharge = pricing.ebikeSurcharge || 0.10;
        
        const baseUnlockCost = totalTrips * unlockFee;
        const baseMinuteCost = totalTrips * avgDuration * perMinuteCost;
        const ebikeSurchargeCost = ebikeTrips * avgDuration * ebikeSurcharge;
        
        const total = baseUnlockCost + baseMinuteCost + ebikeSurchargeCost;
        
        await this.addStep('Action', 'calculator', {
            expression: `${totalTrips} * ${unlockFee} + ${totalTrips} * ${avgDuration} * ${perMinuteCost} + ${ebikeTrips} * ${avgDuration} * ${ebikeSurcharge}`,
            units: 'dollars'
        });
        
        return {
            unlockFees: baseUnlockCost,
            minuteCharges: baseMinuteCost,
            ebikeSurcharges: ebikeSurchargeCost,
            total: total,
            perTrip: total / totalTrips
        };
    }

    /**
     * Calculate membership costs
     * @param {Object} tripAnalysis - Trip analysis
     * @param {Object} pricing - Pricing information
     * @returns {Object} Membership cost breakdown
     */
    async calculateMembershipCost(tripAnalysis, pricing) {
        const membershipPrice = pricing.membershipPrice || 15.00; 
        const includedMinutes = pricing.includedMinutes || 45; 
        const overageFee = pricing.overageFee || 0.15; 
        
        const totalTrips = tripAnalysis.totalTrips;
        const avgDuration = tripAnalysis.avgDuration;
        const totalMinutes = totalTrips * avgDuration;
        
        const overageMinutes = Math.max(0, totalMinutes - (totalTrips * includedMinutes));
        const overageCost = overageMinutes * overageFee;
        
        const total = membershipPrice + overageCost;
        
        await this.addStep('Action', 'calculator', {
            expression: `${membershipPrice} + ${overageMinutes} * ${overageFee}`,
            units: 'dollars'
        });
        
        return {
            membershipFee: membershipPrice,
            overageCharges: overageCost,
            total: total,
            overageMinutes: overageMinutes
        };
    }

    /**
     * Calculate break-even analysis
     * @param {Object} tripAnalysis - Trip analysis
     * @param {Object} pricing - Pricing information
     * @returns {Object} Break-even analysis
     */
    async calculateBreakEven(tripAnalysis, pricing) {
        const membershipPrice = pricing.membershipPrice || 15.00;
        const unlockFee = pricing.unlockFee || 1.00;
        const perMinuteCost = pricing.perMinuteCost || 0.15;
        const avgDuration = tripAnalysis.avgDuration;
        
        const breakEvenTrips = membershipPrice / (unlockFee + avgDuration * perMinuteCost);
        
        await this.addStep('Action', 'calculator', {
            expression: `${membershipPrice} / (${unlockFee} + ${avgDuration} * ${perMinuteCost})`,
            units: 'trips'
        });
        
        return {
            breakEvenTrips: breakEvenTrips,
            actualTrips: tripAnalysis.totalTrips,
            breakEvenMinutes: breakEvenTrips * avgDuration,
            actualMinutes: tripAnalysis.totalTrips * avgDuration
        };
    }

    /**
     * Make final decision based on cost analysis
     * @param {Object} costAnalysis - Cost analysis results
     * @returns {Object} Decision with justification
     */
    makeDecision(costAnalysis) {
        const savings = costAnalysis.savings;
        const breakEven = costAnalysis.breakEven;
        
        let recommendation;
        let justification;
        
        if (savings > 0) {
            recommendation = 'Pay Per Ride/Minute';
            justification = `Pay-per-use is more cost-effective, saving $${savings.toFixed(2)} compared to membership. The break-even point is ${breakEven.breakEvenTrips.toFixed(1)} trips, but you only took ${breakEven.actualTrips} trips.`;
        } else {
            recommendation = 'Buy Monthly Membership';
            justification = `Monthly membership is more cost-effective, saving $${Math.abs(savings).toFixed(2)} compared to pay-per-use. You exceeded the break-even point of ${breakEven.breakEvenTrips.toFixed(1)} trips with your ${breakEven.actualTrips} trips.`;
        }
        
        return {
            recommendation,
            justification
        };
    }

    /**
     * Generate final answer with complete analysis
     * @param {Object} decision - Decision results
     * @param {Object} costAnalysis - Cost analysis
     * @param {Object} pricingInfo - Pricing information
     * @returns {string} Final answer
     */
    generateFinalAnswer(decision, costAnalysis, pricingInfo) {
        return `Based on the analysis of your trip data and the current pricing policy:

**Recommendation: ${decision.recommendation}**

**Justification:** ${decision.justification}

**Cost Breakdown:**
- Pay-per-use total: $${costAnalysis.payPerUse.total.toFixed(2)}
- Membership total: $${costAnalysis.membership.total.toFixed(2)}
- Break-even point: ${costAnalysis.breakEven.breakEvenTrips.toFixed(1)} trips

**Citations:** Analysis based on pricing policy retrieved from ${pricingInfo.citations[0].url} on ${new Date(pricingInfo.citations[0].date).toLocaleDateString()}.`;
    }

    /**
     * Add a step to the agent's execution log
     * @param {string} type - Step type (Thought, Action, Observation, Final Answer)
     * @param {string} content - Step content
     * @param {Object} toolArgs - Tool arguments (for Action steps)
     */
    async addStep(type, content, toolArgs = null) {
        const step = {
            type,
            content,
            toolArgs,
            timestamp: new Date().toISOString()
        };
        
        this.steps.push(step);
        
        console.log(`[${type}] ${content}`);
        if (toolArgs) {
            console.log(`  Tool Args:`, toolArgs);
        }
    }

    cleanup() {
        this.csvTool.close();
        this.policyTool.clearCache();
    }
}

module.exports = ReActBikeShareAgent;
