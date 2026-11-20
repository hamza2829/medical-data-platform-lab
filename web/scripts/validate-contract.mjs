import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from 'yaml';

const here = path.dirname(fileURLToPath(import.meta.url));
const openapiPath = path.resolve(here, '../../docs/openapi.yaml');
const schemaPath = path.resolve(here, '../../schemas/fhir-r4-demo.schema.json');
const openapi = parse(fs.readFileSync(openapiPath, 'utf8'));
const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));

if (openapi.openapi !== '3.1.0') throw new Error('The API description must use OpenAPI 3.1.0.');
for (const endpoint of ['/auth/token/', '/patients/', '/observations/', '/devices/', '/exports/pseudonymized/', '/users/']) {
  if (!(endpoint in openapi.paths)) throw new Error(`Missing documented API path: ${endpoint}`);
}
for (const type of ['Patient', 'Observation', 'Device']) {
  if (!(type in schema.$defs)) throw new Error(`Missing versioned FHIR schema: ${type}`);
}
console.log('OpenAPI and versioned FHIR schema are valid.');
