import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Ramp-up
    { duration: '3m', target: 50 },   // Steady state
    { duration: '1m', target: 100 },  // Spike
    { duration: '2m', target: 100 },  // Sustained spike
    { duration: '1m', target: 0 },    // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.05'],
    errors: ['rate<0.1'],
  },
};

const BASE_URL = __ENV.TARGET_URL || 'https://api-staging.boltchats.example.com';

export default function () {
  // Health check
  let res = http.get(`${BASE_URL}/health`);
  let success = check(res, {
    'health check status 200': (r) => r.status === 200,
    'health check response time < 200ms': (r) => r.timings.duration < 200,
  });
  errorRate.add(!success);

  sleep(1);

  // Register user
  const username = `user_${Date.now()}_${Math.random().toString(36).substring(7)}`;
  const email = `${username}@example.com`;
  const password = 'Test1234!';

  res = http.post(
    `${BASE_URL}/api/v1/auth/register`,
    JSON.stringify({ username, email, password }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  success = check(res, {
    'register status 200': (r) => r.status === 200,
    'register has access_token': (r) => r.json('access_token') !== undefined,
  });
  errorRate.add(!success);

  if (!success) return;

  const token = res.json('access_token');

  sleep(1);

  // Get rooms
  res = http.get(`${BASE_URL}/api/v1/rooms`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  success = check(res, {
    'rooms status 200': (r) => r.status === 200,
    'rooms response is array': (r) => Array.isArray(r.json()),
  });
  errorRate.add(!success);

  sleep(2);
}

export function handleSummary(data) {
  return {
    'summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, options) {
  const indent = options?.indent || '';
  let output = '\n';
  output += `${indent}✓ checks.............: ${(data.metrics.checks.values.rate * 100).toFixed(2)}%\n`;
  output += `${indent}✓ http_req_duration..: avg=${data.metrics.http_req_duration.values.avg.toFixed(2)}ms p(95)=${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  output += `${indent}✓ http_req_failed....: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%\n`;
  output += `${indent}✓ iterations.........: ${data.metrics.iterations.values.count}\n`;
  return output;
}
