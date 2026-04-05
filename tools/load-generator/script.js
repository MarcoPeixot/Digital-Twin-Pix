// k6 placeholder - sera expandido em tarefas futuras
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 1,
  duration: '5s',
};

export default function () {
  const res = http.get('http://localhost:8080/health');
  check(res, { 'status is 200': (r) => r.status === 200 });
}
