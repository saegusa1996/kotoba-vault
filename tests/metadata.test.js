"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const readJson = (name) => JSON.parse(fs.readFileSync(path.join(root, name), "utf8"));

test("release metadata stays aligned", () => {
  const manifest = readJson("manifest.json");
  const packageJson = readJson("package.json");
  const versions = readJson("versions.json");

  assert.equal(manifest.id, "kotoba-vault");
  assert.equal(packageJson.version, manifest.version);
  assert.equal(versions[manifest.version], manifest.minAppVersion);
});

test("committed plugin entry point is a self-contained bundle", () => {
  const bundle = fs.readFileSync(path.join(root, "main.js"), "utf8");
  assert.match(bundle, /require\(["']obsidian["']\)/);
  assert.doesNotMatch(bundle, /require\(["']\.\/src\//);
});
