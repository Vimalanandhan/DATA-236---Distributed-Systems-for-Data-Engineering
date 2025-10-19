/**
 * @jest-environment node
 */
const { JSDOM } = require('jsdom');
const util = require('util');
global.TextEncoder = util.TextEncoder;
global.TextDecoder = util.TextDecoder;

import Header from '../Header';
import React from 'react';
import { render } from '@testing-library/react';
import { getByText } from '@testing-library/dom';
import '@testing-library/jest-dom';

describe('UI Tests', () => {
    it('should display the correct heading in the Header component', () => {
        const dom = new JSDOM(`<!DOCTYPE html><html><head></head><body><div id="root"></div></body></html>`, {
            url: 'http://localhost:3000'
        });
        global.document = dom.window.document;
        global.window = dom.window;
        const { container } = render(<Header />, { container: dom.window.document.body });
        const headingElement = getByText(dom.window.document.body, /Product Inventory/i);
        expect(headingElement).toBeInTheDocument();
    });
});
