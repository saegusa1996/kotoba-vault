"use strict";

const GOJUON_FOLDERS = Object.freeze(
  [..."あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"]
);
const GOJUON_SET = new Set(GOJUON_FOLDERS);

const BASE_KANA = Object.freeze({
  が: "か", ぎ: "き", ぐ: "く", げ: "け", ご: "こ",
  ざ: "さ", じ: "し", ず: "す", ぜ: "せ", ぞ: "そ",
  だ: "た", ぢ: "ち", づ: "つ", で: "て", ど: "と",
  ば: "は", び: "ひ", ぶ: "ふ", べ: "へ", ぼ: "ほ",
  ぱ: "は", ぴ: "ひ", ぷ: "ふ", ぺ: "へ", ぽ: "ほ",
  ゔ: "う",
  ぁ: "あ", ぃ: "い", ぅ: "う", ぇ: "え", ぉ: "お",
  っ: "つ", ゃ: "や", ゅ: "ゆ", ょ: "よ", ゎ: "わ",
  ゕ: "か", ゖ: "け",
});

function katakanaToHiragana(value) {
  return String(value ?? "")
    .normalize("NFKC")
    .replace(/[ァ-ヶ]/g, (character) =>
      String.fromCharCode(character.charCodeAt(0) - 0x60)
    );
}

function folderFromReading(value) {
  const values = Array.isArray(value) ? value : [value];
  for (const item of values) {
    const normalized = katakanaToHiragana(item).trim();
    const match = normalized.match(/[ぁ-ゖ]/);
    if (!match) continue;
    const folder = BASE_KANA[match[0]] || match[0];
    if (GOJUON_SET.has(folder)) return folder;
  }
  return null;
}

function cleanVaultPath(value) {
  const normalized = String(value ?? "")
    .replace(/\\/g, "/")
    .replace(/\/{2,}/g, "/")
    .replace(/^\/+|\/+$/g, "")
    .trim();
  if (!normalized || normalized.includes("\0")) return "";

  const parts = [];
  for (const part of normalized.split("/")) {
    if (!part || part === ".") continue;
    if (part === "..") return "";
    parts.push(part);
  }
  return parts.join("/");
}

function isPathWithin(path, root) {
  const normalizedPath = cleanVaultPath(path);
  const normalizedRoot = cleanVaultPath(root);
  return Boolean(
    normalizedPath &&
      normalizedRoot &&
      (normalizedPath === normalizedRoot ||
        normalizedPath.startsWith(`${normalizedRoot}/`))
  );
}

module.exports = {
  BASE_KANA,
  GOJUON_FOLDERS,
  cleanVaultPath,
  folderFromReading,
  isPathWithin,
  katakanaToHiragana,
};
