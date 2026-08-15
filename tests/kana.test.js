"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const {
  cleanVaultPath,
  folderFromReading,
  isPathWithin,
  katakanaToHiragana,
} = require("../src/kana");

test("normalizes katakana", () => {
  assert.equal(katakanaToHiragana("パーティー"), "ぱーてぃー");
});

test("maps readings to base gojuon folders", () => {
  const cases = new Map([
    ["あたためる", "あ"],
    ["学校", null],
    ["がっこう", "か"],
    ["パーティー", "は"],
    ["ちょっと", "ち"],
    [["", "ヴァイオリン", "バイオリン"], "う"],
  ]);
  for (const [reading, expected] of cases) {
    assert.equal(folderFromReading(reading), expected);
  }
});

test("cleans vault-relative paths", () => {
  assert.equal(cleanVaultPath("/Japanese\\Words//"), "Japanese/Words");
  assert.equal(cleanVaultPath("Japanese/./Words"), "Japanese/Words");
  assert.equal(cleanVaultPath("Japanese/../Secrets"), "");
  assert.equal(cleanVaultPath(""), "");
});

test("checks path boundaries by complete segment", () => {
  assert.equal(isPathWithin("Japanese/Words/あ/note.md", "Japanese/Words"), true);
  assert.equal(isPathWithin("Japanese/Words", "Japanese/Words"), true);
  assert.equal(isPathWithin("Japanese/Words-old/note.md", "Japanese/Words"), false);
  assert.equal(isPathWithin("../Japanese/Words", "Japanese/Words"), false);
});
