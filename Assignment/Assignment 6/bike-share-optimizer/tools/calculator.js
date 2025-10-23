class CalculatorTool {
    constructor() {
        this.allowedPattern = /^[0-9+\-*/().\s]+$/;
    }

    /**
     * Calculate the result of a mathematical expression
     * @param {string} expression - Mathematical expression to evaluate
     * @param {string} units - Optional units for the result
     * @returns {Object} Result with success, data, error, source, ts
     */
    async calculate(expression, units = null) {
        try {
            if (!expression || typeof expression !== 'string') {
                return {
                    success: false,
                    error: "Expression must be a non-empty string",
                    source: "calculator",
                    ts: new Date().toISOString()
                };
            }

            if (!this.allowedPattern.test(expression)) {
                return {
                    success: false,
                    error: "Expression contains invalid characters. Only numbers, +, -, *, /, (, ), and spaces are allowed.",
                    source: "calculator",
                    ts: new Date().toISOString()
                };
            }

            const result = this.safeEvaluate(expression);

            if (isNaN(result)) {
                return {
                    success: false,
                    error: "Expression resulted in NaN (Not a Number)",
                    source: "calculator",
                    ts: new Date().toISOString()
                };
            }

            if (!isFinite(result)) {
                return {
                    success: false,
                    error: "Expression resulted in infinity",
                    source: "calculator",
                    ts: new Date().toISOString()
                };
            }

            return {
                success: true,
                data: {
                    value: result,
                    units: units || undefined
                },
                source: "calculator",
                ts: new Date().toISOString()
            };

        } catch (error) {
            return {
                success: false,
                error: `Calculation error: ${error.message}`,
                source: "calculator",
                ts: new Date().toISOString()
            };
        }
    }

    /**
     * Safely evaluate a mathematical expression without using eval()
     * @param {string} expression - Mathematical expression
     * @returns {number} Result of the calculation
     */
    safeEvaluate(expression) {
        const cleanExpression = expression.replace(/\s/g, '');
        
        return this.evaluateExpression(cleanExpression);
    }

    /**
     * Recursive descent parser for mathematical expressions
     * @param {string} expr - Expression to evaluate
     * @returns {number} Result
     */
    evaluateExpression(expr) {
        // Remove parentheses and evaluate recursively
        while (expr.includes('(')) {
            const lastOpen = expr.lastIndexOf('(');
            const closeParen = expr.indexOf(')', lastOpen);
            
            if (closeParen === -1) {
                throw new Error('Mismatched parentheses');
            }
            
            const innerExpr = expr.substring(lastOpen + 1, closeParen);
            const innerResult = this.evaluateExpression(innerExpr);
            
            expr = expr.substring(0, lastOpen) + innerResult + expr.substring(closeParen + 1);
        }
        
        return this.evaluateAdditionSubtraction(expr);
    }

    /**
     * Evaluate addition and subtraction (lowest precedence)
     * @param {string} expr - Expression to evaluate
     * @returns {number} Result
     */
    evaluateAdditionSubtraction(expr) {
        let result = this.evaluateMultiplicationDivision(expr);
        
        for (let i = 0; i < expr.length; i++) {
            if (expr[i] === '+' || expr[i] === '-') {
                const left = expr.substring(0, i);
                const right = expr.substring(i + 1);
                
                if (left && right) {
                    const leftResult = this.evaluateMultiplicationDivision(left);
                    const rightResult = this.evaluateMultiplicationDivision(right);
                    
                    if (expr[i] === '+') {
                        result = leftResult + rightResult;
                    } else {
                        result = leftResult - rightResult;
                    }
                }
            }
        }
        
        return result;
    }

    /**
     * Evaluate multiplication and division (higher precedence)
     * @param {string} expr - Expression to evaluate
     * @returns {number} Result
     */
    evaluateMultiplicationDivision(expr) {
        let result = this.evaluateNumber(expr);
        
        for (let i = 0; i < expr.length; i++) {
            if (expr[i] === '*' || expr[i] === '/') {
                const left = expr.substring(0, i);
                const right = expr.substring(i + 1);
                
                if (left && right) {
                    const leftResult = this.evaluateNumber(left);
                    const rightResult = this.evaluateNumber(right);
                    
                    if (expr[i] === '*') {
                        result = leftResult * rightResult;
                    } else {
                        if (rightResult === 0) {
                            throw new Error('Division by zero');
                        }
                        result = leftResult / rightResult;
                    }
                }
            }
        }
        
        return result;
    }

    /**
     * Evaluate a number or handle negative numbers
     * @param {string} expr - Expression to evaluate
     * @returns {number} Result
     */
    evaluateNumber(expr) {
        if (expr.startsWith('-')) {
            return -this.evaluateNumber(expr.substring(1));
        }
        
        // Parse decimal number
        const num = parseFloat(expr);
        if (isNaN(num)) {
            throw new Error(`Invalid number: ${expr}`);
        }
        
        return num;
    }
}

module.exports = CalculatorTool;
