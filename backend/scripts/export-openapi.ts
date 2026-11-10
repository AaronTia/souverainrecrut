import { mkdirSync, writeFileSync } from "node:fs";
import { swaggerSpec } from "../src/docs/swagger";

const output = process.argv[2] ?? "reports/openapi.json";

mkdirSync("reports", { recursive: true });
writeFileSync(output, JSON.stringify(swaggerSpec, null, 2) + "\n");
console.log(`Spécification OpenAPI écrite dans ${output}`);
