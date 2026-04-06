import http from 'k6/http';
import { check } from 'k6';

function parseJsonEnv(name, fallback) {
  try {
    return __ENV[name] ? JSON.parse(__ENV[name]) : fallback;
  } catch (error) {
    return fallback;
  }
}

const loadProfile = parseJsonEnv('LOAD_PROFILE_JSON', {
  type: 'constant-vus',
  vus: 1,
  duration: '5s',
});

const destinationKeys = parseJsonEnv('DESTINATION_KEYS_JSON', [
  'email@example.com',
]);

export const options = {
  scenarios: {
    transactions: loadProfile.type === 'ramping-vus'
      ? {
          executor: 'ramping-vus',
          startVUs: loadProfile.start_vus || 1,
          gracefulRampDown: loadProfile.graceful_ramp_down || '0s',
          stages: loadProfile.stages || [{ duration: '5s', target: 1 }],
        }
      : {
          executor: 'constant-vus',
          vus: loadProfile.vus || 1,
          duration: loadProfile.duration || '5s',
        },
  },
};

export default function () {
  const baseUrl = __ENV.TARGET_BASE_URL || 'http://localhost:8080';
  const payload = JSON.stringify({
    sourceKey: __ENV.SOURCE_KEY || '11111111111',
    destinationKey: destinationKeys[__ITER % destinationKeys.length],
    amount: Number(__ENV.TRANSACTION_AMOUNT || '10.5'),
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    tags: {
      scenario_type: loadProfile.type,
    },
  };

  const res = http.post(`${baseUrl}/transactions`, payload, params);
  check(res, {
    'status is 200, 500 or 503': (r) => r.status === 200 || r.status === 500 || r.status === 503,
  });
}
