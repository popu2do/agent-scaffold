#!/usr/bin/env node
// Drives a local CLIProxyAPI chat-completions endpoint that returns images as data URIs.
// Usage:
//   node generate.mjs <prompt> [--ref <image>] [--out <file>] [--base <url>] [--key <api-key>]
// Prints one JSON line on success: { file, bytes, model, elapsed_ms }

import { writeFile, mkdir, readFile } from "node:fs/promises";
import { dirname, resolve, extname, join } from "node:path";
import { homedir } from "node:os";

const DEFAULT_MODEL = "gemini-3.1-flash-image";
const DEFAULT_BASE = "http://127.0.0.1:8317/v1";
const TIMEOUT_MS = 120_000;

const FLAGS = new Set(["--out", "--base", "--key", "--model", "--ref"]);

function fail(code, message) {
  console.error(message);
  process.exit(code);
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

// The DSH credential file already stores the key, so read it rather than making every
// caller pass the secret again. The shell environment does not carry it.
async function keyFromDshCredentials() {
  try {
    const text = await readFile(join(homedir(), ".dsh", ".credentials.yaml"), "utf8");
    return text.match(/^\s*EASYCLIPROXYAPI_API_KEY:\s*(\S+)\s*$/m)?.[1];
  } catch {
    return undefined;
  }
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
    bytes = await readFile(resolve(refPath));
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

const base = (flags.base ?? process.env.CPA_BASE_URL ?? DEFAULT_BASE).replace(/\/+$/, "");
const url = `${base}/chat/completions`;
const model = flags.model ?? DEFAULT_MODEL;
const outArg = flags.out ?? join(homedir(), ".dsh", "outputs", "images", `image-${Date.now()}.jpg`);
const key = flags.key ?? process.env.EASYCLIPROXYAPI_API_KEY ?? (await keyFromDshCredentials());
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
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
} catch (error) {
  if (error?.name === "TimeoutError") {
    fail(1, `gateway timed out after ${TIMEOUT_MS / 1000}s at ${url}`);
  }
  fail(1, `gateway unreachable at ${url}; is CLIProxyAPI listening? (${error?.cause?.code ?? error?.message})`);
}

if (!res.ok) {
  const body = await res.text();
  console.error(`HTTP ${res.status}: ${body.slice(0, 800)}`);
  if (/User location is not supported/i.test(body)) {
    console.error("Hint: egress is not proxied. Check proxy-url in the CLIProxyAPI config, expected http://127.0.0.1:9468, and confirm that port is listening.");
  }
  if (/Invalid API key|Missing API key|Unauthorized/i.test(body)) {
    console.error("Hint: the API key is missing or wrong. Confirm EASYCLIPROXYAPI_API_KEY in ~/.dsh/.credentials.yaml, or pass --key.");
  }
  process.exit(1);
}

const payload = await res.json();
const uri = payload?.choices?.[0]?.message?.images?.[0]?.image_url?.url ?? "";
if (!uri) {
  // A reasoning-only reply means the request reached a protocol that drops images, or the
  // model id is text-only. Treating that as success would hand back an empty file name.
  const keys = Object.keys(payload?.choices?.[0]?.message ?? {}).join(",");
  fail(1, `no image in response; message fields were [${keys}]. This model returns images only through /v1/chat/completions.`);
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
