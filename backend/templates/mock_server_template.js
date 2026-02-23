/**
 * Self-contained Node.js HTTP mock server.
 *
 * Uses only Node.js stdlib (http, url).  Routes and responses are injected
 * at generation time by replacing the __ROUTES_PLACEHOLDER__ token.
 *
 * Usage:  node mock_server.js
 *         (PORT is baked in at generation time via __PORT_PLACEHOLDER__)
 */

const http = require('http');
const url = require('url');

const PORT = parseInt(process.env.PORT || '__PORT_PLACEHOLDER__', 10) || 9100;
const ROUTES = __ROUTES_PLACEHOLDER__;

// ---------------------------------------------------------------------------
// Route matching (supports path parameters like :id)
// ---------------------------------------------------------------------------

function matchRoute(method, pathname) {
  for (const route of ROUTES) {
    if (route.method !== method) continue;

    const routeParts = route.path.split('/').filter(Boolean);
    const pathParts = pathname.split('/').filter(Boolean);

    if (routeParts.length !== pathParts.length) continue;

    const params = {};
    let match = true;

    for (let i = 0; i < routeParts.length; i++) {
      if (routeParts[i].startsWith(':')) {
        params[routeParts[i].slice(1)] = decodeURIComponent(pathParts[i]);
      } else if (routeParts[i] !== pathParts[i]) {
        match = false;
        break;
      }
    }

    if (match) {
      return { route, params };
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Mock data helpers
// ---------------------------------------------------------------------------

/**
 * Inject path params into mock response.
 * If the response is an object with an "id" field and params has "id",
 * replace the mock id with the actual param value.
 */
function injectParams(response, params) {
  if (!response || typeof response !== 'object') return response;

  const result = Array.isArray(response)
    ? response.map(item => injectParams(item, params))
    : { ...response };

  if (!Array.isArray(result)) {
    for (const [key, value] of Object.entries(params)) {
      if (key in result) {
        // Try to preserve type
        const numVal = Number(value);
        result[key] = isNaN(numVal) ? value : numVal;
      }
    }
  }

  return result;
}

/**
 * Generate a list response when the route path suggests a collection.
 */
function maybeWrapInList(response, pathname) {
  // If the path ends with a collection name (no param), wrap single object in array
  const parts = pathname.split('/').filter(Boolean);
  const lastPart = parts[parts.length - 1] || '';

  if (!lastPart.startsWith(':') && !response) {
    return [];
  }

  return response;
}

// ---------------------------------------------------------------------------
// Request body parsing
// ---------------------------------------------------------------------------

function parseBody(req) {
  return new Promise((resolve) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => {
      const raw = Buffer.concat(chunks).toString();
      if (!raw) return resolve(null);
      try {
        resolve(JSON.parse(raw));
      } catch {
        resolve(raw);
      }
    });
    req.on('error', () => resolve(null));
  });
}

// ---------------------------------------------------------------------------
// HTTP server
// ---------------------------------------------------------------------------

const server = http.createServer(async (req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With');
  res.setHeader('Access-Control-Max-Age', '86400');

  // Preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    return res.end();
  }

  const parsed = url.parse(req.url, true);
  const pathname = parsed.pathname || '/';
  const query = parsed.query || {};

  // Log request
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${pathname}`);

  // Try to match a route
  const result = matchRoute(req.method, pathname);

  if (result) {
    const { route, params } = result;
    const statusCode = route.status || 200;

    // Parse request body for POST/PUT/PATCH
    let body = null;
    if (['POST', 'PUT', 'PATCH'].includes(req.method)) {
      body = await parseBody(req);
    }

    // Build response
    let responseData = route.response;

    // Inject path params
    responseData = injectParams(responseData, params);

    // For POST requests, merge request body into response (echo back)
    if (req.method === 'POST' && body && typeof body === 'object' && typeof responseData === 'object' && !Array.isArray(responseData)) {
      responseData = { ...responseData, ...body, id: responseData.id || Math.floor(Math.random() * 10000) };
    }

    // Apply query param filtering for GET list endpoints
    if (req.method === 'GET' && Array.isArray(responseData) && Object.keys(query).length > 0) {
      // Simple pagination
      const page = parseInt(query.page) || 1;
      const limit = parseInt(query.limit || query.per_page) || 10;
      const start = (page - 1) * limit;
      // Don't actually slice our mock data (usually just 1 item), but add pagination headers
      res.setHeader('X-Total-Count', String(responseData.length));
      res.setHeader('X-Page', String(page));
      res.setHeader('X-Per-Page', String(limit));
    }

    // Add artificial latency to simulate real API (50-200ms)
    const delay = 50 + Math.floor(Math.random() * 150);
    await new Promise(resolve => setTimeout(resolve, delay));

    res.writeHead(statusCode, { 'Content-Type': 'application/json' });

    if (statusCode === 204) {
      res.end();
    } else {
      const jsonBody = typeof responseData === 'string'
        ? JSON.stringify({ data: responseData })
        : JSON.stringify(responseData, null, 2);
      res.end(jsonBody);
    }
  } else {
    // 404 — list available routes
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      error: 'Not Found',
      path: pathname,
      method: req.method,
      available_routes: ROUTES.map(r => `${r.method} ${r.path} - ${r.summary || '(no summary)'}`),
    }, null, 2));
  }
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('Received SIGTERM, shutting down gracefully...');
  server.close(() => process.exit(0));
});

process.on('SIGINT', () => {
  console.log('Received SIGINT, shutting down...');
  server.close(() => process.exit(0));
});

// Start listening
server.listen(PORT, () => {
  console.log(`Mock server running on http://localhost:${PORT}`);
  console.log(`Serving ${ROUTES.length} route(s):`);
  ROUTES.forEach(r => {
    console.log(`  ${r.method.padEnd(7)} ${r.path}  ${r.summary ? '— ' + r.summary : ''}`);
  });
  console.log('');
});
