import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require = createRequire(new URL('../dashboard/kindle-ai-usage/package.json', import.meta.url));
const sharp = require('sharp');

const out = path.dirname(fileURLToPath(import.meta.url));
const W = 1448, H = 1072, cx = 724, cy = 470;
const lengths = [300, 250, 285, 230, 310, 260, 240, 295, 225, 275, 255, 290];
const rays = lengths.map((len, i) => {
  const angle = i * 30 + (i % 2 ? 7 : -4);
  return `<path d="M -38 0 L 38 0 L 16 ${-len} A 16 16 0 0 0 -16 ${-len} Z" transform="translate(${cx} ${cy}) rotate(${angle})"/>`;
}).join('');

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
  <rect width="${W}" height="${H}" fill="#ffffff"/>
  <g fill="#1a1a1a">${rays}<circle cx="${cx}" cy="${cy}" r="62"/></g>
  <text x="${cx}" y="960" text-anchor="middle" font-family="Georgia, serif" font-size="120" fill="#1a1a1a">Claude</text>
</svg>`;

const landscape = await sharp(Buffer.from(svg)).grayscale().png().toBuffer();
await sharp(landscape).toFile(out + '/claude-landscape.png');
await sharp(landscape).rotate(270).grayscale().toColourspace('b-w').png().toFile(out + '/claude-kindle.png');
