#!/usr/bin/env node
// Generates images through a locally configured CLIProxyAPI gateway.
// Usage:
//   node generate.mjs <prompt> [--ref <image>] [--out <file>] [--base <url>] [--key <api-key>] [--model <id>]
// Gateway settings live in config.json next to this skill, copied from assets/config.template.json.
// Prints one JSON line on success: { file, bytes, model, elapsed_ms }

import { writeFile, mkdir, readFile } from "node:fs/promises";
import { dirname, resolve, extname, join } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";

const SKILL_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CONFIG_PATH = process.env.CPA_IMAGE_GEN_CONFIG ?? join(SKILL_DIR, "config.json");
const FLAGS = new Set(["--out", "--base", "--key", "--model", "--ref"]);

function fail(code, message) {
  console.error(message);
  process.exit(code);
}

// Expanding ~ here keeps paths in the config portable across the Windows and Linux installs
// the same skill gets copied to.
function expandHome(p) {
  return p.startsWith("~/") ? join(homedir(), p.slice(2)) : p;
}

async function loadConfig() {
  let text;
  try {
    text = await readFile(CONFIG_PATH, "utf8");
  } catch {
    fail(2, `missing gateway config: ${CONFIG_PATH}. Copy assets/config.template.json to config.json and fill it in.`);
  }
  let config;
  try {
    config = JSON.parse(text);
  } catch (error) {
    fail(2, `config.json is not valid JSON: ${error.message}`);
  }
  for (const key of ["baseUrl", "model"]) {
    if (!config[key]) fail(2, `config.json is missing "${key}"`);
  }
  return config;
}

// The key may sit in the config, in an environment variable, or in a credential file that
// already holds it. Whichever the config names is the one that gets used.
async function resolveKey(config) {
  if (config.apiKey) return config.apiKey;
  if (config.apiKeyEnv && process.env[config.apiKeyEnv]) return process.env[config.apiKeyEnv];
  if (config.credentialsFile && config.credentialsKey) {
    try {
      const text = await readFile(expandHome(config.credentialsFile), "utf8");
      const pattern = new RegExp(`^\\s*${config.credentialsKey}:\\s*(\\S+)\\s*$`, "m");
      const match = text.match(pattern);
      if (match) return match[1];
    } catch {
      return undefined;
    }
  }
  return undefined;
}

function parseArgs(argv) {
  const prompt = [];
  const flags = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!FLAGS.has(arg)) {
      prompt.push(arg);
      continue;
    }
    const value = argv[i + 1];
    // A flag without a value silently falling back to a default is how files land in
    // unexpected directories, so refuse instead of guessing.
    if (value === undefined || value.startsWith("--")) fail(2, `${arg} needs a value`);
    flags[arg.slice(2)] = value;
    i += 1;
  }
  return { prompt: prompt.join(" ").trim(), flags };
}

function mimeOf(path) {
  const ext = extname(path).toLowerCase();
  if (ext === ".png") return "image/png";
  if (ext === ".webp") return "image/webp";
  if (ext === ".gif") return "image/gif";
  return "image/jpeg";
}

// A reference image turns the call into an edit: the prompt then describes the change
// while the model keeps the source composition.
async function contentFor(prompt, refPath) {
  if (!refPath) return prompt;
  let bytes;
  try {
    bytes = await readFile(resolve(expandHome(refPath)));
  } catch {
    fail(1, `cannot read reference image: ${refPath}`);
  }
  const dataUri = `data:${mimeOf(refPath)};base64,${bytes.toString("base64")}`;
  return [
    { type: "text", text: prompt },
    { type: "image_url", image_url: { url: dataUri } },
  ];
}

const { prompt, flags } = parseArgs(process.argv.slice(2));
if (!prompt) {
  fail(2, "usage: node generate.mjs <prompt> [--ref <image>] [--out <file>] [--base <url>] [--key <api-key>] [--model <id>]");
}

const config = await loadConfig();
const base = (flags.base ?? process.env.CPA_IMAGE_GEN_BASE ?? config.baseUrl).replace(/\/+$/, "");
const url = `${base}/chat/completions`;
const model = flags.model ?? config.model;
const timeoutMs = Number(config.timeoutMs ?? 120_000);
const outputDir = expandHome(config.outputDir ?? "~/.dsh/outputs/images");
const outArg = flags.out ?? join(outputDir, `image-${Date.now()}.jpg`);
const key = flags.key ?? (await resolveKey(config));
const content = await contentFor(prompt, flags.ref);

const started = Date.now();
let res;
try {
  res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(key ? { Authorization: `Bearer ${key}` } : {}),
    },
    body: JSON.stringify({ model, messages: [{ role: "user", content }], stream: false }),
    signal: AbortSignal.timeout(timeoutMs),
  });
} catch (error) {
  if (error?.name === "TimeoutError") {
    fail(1, `gateway timed out after ${timeoutMs / 1000}s at ${url}`);
  }
  fail(1, `gateway unreachable at ${url}; is the gateway listening? (${error?.cause?.code ?? error?.message})`);
}

if (!res.ok) {
  const body = await res.text();
  console.error(`HTTP ${res.status}: ${body.slice(0, 800)}`);
  if (/User location is not supported/i.test(body)) {
    console.error("Hint: egress is not proxied. Check the gateway's proxy setting and confirm that proxy port is listening.");
  }
  if (/Invalid API key|Missing API key|Unauthorized/i.test(body)) {
    console.error(`Hint: the API key is missing or wrong. Check the key source named in ${CONFIG_PATH}, or pass --key.`);
  }
  process.exit(1);
}

const payload = await res.json();
const uri = payload?.choices?.[0]?.message?.images?.[0]?.image_url?.url ?? "";
if (!uri) {
  // A reasoning-only reply means the request reached a protocol that drops images, or the
  // model id is text-only. Treating that as success would hand back an empty file name.
  const fields = Object.keys(payload?.choices?.[0]?.message ?? {}).join(",");
  fail(1, `no image in response; message fields were [${fields}]. This gateway returns images only through /v1/chat/completions.`);
}

const comma = uri.indexOf(",");
if (comma < 0) fail(1, "image entry is not a data URI");

// Take the extension from the payload instead of assuming jpeg, so a png-returning model
// does not produce a file whose bytes disagree with its name.
const mime = uri.slice(5, uri.indexOf(";")) || "image/jpeg";
const ext = mime === "image/png" ? ".png" : mime === "image/webp" ? ".webp" : ".jpg";
const target = resolve(extname(outArg) ? outArg : outArg + ext);

await mkdir(dirname(target), { recursive: true });
const bytes = Buffer.from(uri.slice(comma + 1), "base64");
await writeFile(target, bytes);

console.log(JSON.stringify({ file: target, bytes: bytes.length, model, elapsed_ms: Date.now() - started }));
