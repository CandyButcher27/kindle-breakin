import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';

const file = process.argv[2];
createServer((request, response) => {
  response.writeHead(200, { 'content-type': 'image/png' });
  response.end(readFileSync(file));
}).listen(8787, '127.0.0.1', () => console.log(`serving ${file} on :8787`));
