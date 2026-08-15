"use strict";

const {
  Notice,
  Plugin,
  PluginSettingTab,
  Setting,
  TFile,
  TFolder,
  normalizePath,
} = require("obsidian");
const { cleanVaultPath, folderFromReading, isPathWithin } = require("./kana");

const DEFAULT_SETTINGS = Object.freeze({
  wordRoot: "Japanese/Words",
  inboxFolder: "Japanese/Inbox",
  readingProperty: "reading",
  autoSort: true,
  sortInboxOnStartup: true,
  debounceMs: 500,
});

class KotobaVaultSettingTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();

    new Setting(containerEl)
      .setName("Vocabulary root")
      .setDesc("Destination root containing the gojūon folders.")
      .addText((text) =>
        text
          .setPlaceholder("Japanese/Words")
          .setValue(this.plugin.settings.wordRoot)
          .onChange((value) =>
            this.plugin.updatePathSetting("wordRoot", value, "Vocabulary root")
          )
      );

    new Setting(containerEl)
      .setName("Vocabulary inbox")
      .setDesc("New notes in this folder are moved after reading is added.")
      .addText((text) =>
        text
          .setPlaceholder("Japanese/Inbox")
          .setValue(this.plugin.settings.inboxFolder)
          .onChange((value) =>
            this.plugin.updatePathSetting("inboxFolder", value, "Vocabulary inbox")
          )
      );

    new Setting(containerEl)
      .setName("Reading property")
      .setDesc("Frontmatter property used as the filing source of truth.")
      .addText((text) =>
        text
          .setPlaceholder("reading")
          .setValue(this.plugin.settings.readingProperty)
          .onChange(async (value) => {
            this.plugin.settings.readingProperty = value.trim() || "reading";
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("Metadata debounce")
      .setDesc("Wait 100–5000 ms before filing after a metadata change.")
      .addText((text) =>
        text
          .setPlaceholder("500")
          .setValue(String(this.plugin.settings.debounceMs))
          .onChange(async (value) => {
            const parsed = Number(value);
            if (!Number.isFinite(parsed)) return;
            this.plugin.settings.debounceMs = Math.min(5000, Math.max(100, parsed));
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("Sort automatically")
      .setDesc("Move managed notes after their reading metadata changes.")
      .addToggle((toggle) =>
        toggle.setValue(this.plugin.settings.autoSort).onChange(async (value) => {
          this.plugin.settings.autoSort = value;
          await this.plugin.saveSettings();
        })
      );

    new Setting(containerEl)
      .setName("Sort inbox on startup")
      .setDesc("Checks only direct Markdown children after the layout is ready.")
      .addToggle((toggle) =>
        toggle
          .setValue(this.plugin.settings.sortInboxOnStartup)
          .onChange(async (value) => {
            this.plugin.settings.sortInboxOnStartup = value;
            await this.plugin.saveSettings();
          })
      );
  }
}

module.exports = class KotobaVault extends Plugin {
  async onload() {
    await this.loadSettings();
    this.pending = new Map();
    this.moving = new Set();
    this.addSettingTab(new KotobaVaultSettingTab(this.app, this));

    this.registerEvent(
      this.app.metadataCache.on("changed", (file, _data, cache) => {
        if (!this.settings.autoSort || !(file instanceof TFile)) return;
        if (file.extension !== "md" || !this.isManagedPath(file.path)) return;
        const reading = cache?.frontmatter?.[this.settings.readingProperty];
        if (reading === undefined || reading === null || reading === "") return;
        this.schedule(file.path, reading);
      })
    );

    this.app.workspace.onLayoutReady(() => {
      if (this.settings.sortInboxOnStartup) void this.sortInbox(false);
    });

    this.addCommand({
      id: "preview-vocabulary-inbox",
      name: "Preview vocabulary inbox filing",
      callback: () => void this.previewInbox(),
    });

    this.addCommand({
      id: "sort-current-note-by-reading",
      name: "Sort current vocabulary note by reading",
      callback: () => void this.sortCurrentNote(),
    });

    this.addCommand({
      id: "sort-vocabulary-inbox",
      name: "Sort all vocabulary notes in inbox",
      callback: () => void this.sortInbox(true),
    });
  }

  onunload() {
    for (const timer of this.pending.values()) window.clearTimeout(timer);
    this.pending.clear();
    this.moving.clear();
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    this.settings.wordRoot =
      cleanVaultPath(this.settings.wordRoot) || DEFAULT_SETTINGS.wordRoot;
    this.settings.inboxFolder =
      cleanVaultPath(this.settings.inboxFolder) || DEFAULT_SETTINGS.inboxFolder;
    this.settings.readingProperty =
      String(this.settings.readingProperty || "").trim() || "reading";
    this.settings.debounceMs = Math.min(
      5000,
      Math.max(100, Number(this.settings.debounceMs) || DEFAULT_SETTINGS.debounceMs)
    );
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  async updatePathSetting(key, value, label) {
    const cleaned = cleanVaultPath(value);
    if (!cleaned) {
      new Notice(`${label} must be a non-empty vault-relative path.`);
      return;
    }
    this.settings[key] = cleaned;
    await this.saveSettings();
  }

  isManagedPath(path) {
    const normalized = cleanVaultPath(path);
    const inbox = this.settings.inboxFolder;
    const parent = normalized.slice(0, normalized.lastIndexOf("/"));
    return isPathWithin(normalized, this.settings.wordRoot) || parent === inbox;
  }

  readingFor(file) {
    return this.app.metadataCache.getFileCache(file)?.frontmatter?.[
      this.settings.readingProperty
    ];
  }

  directInboxNotes() {
    const folder = this.app.vault.getAbstractFileByPath(this.settings.inboxFolder);
    if (!(folder instanceof TFolder)) return [];
    return folder.children.filter(
      (child) => child instanceof TFile && child.extension === "md"
    );
  }

  planFor(file, reading = this.readingFor(file)) {
    const folder = folderFromReading(reading);
    if (!folder) return { file, folder: null, destination: null, collision: false };
    const destination = normalizePath(
      `${this.settings.wordRoot}/${folder}/${file.name}`
    );
    const existing = this.app.vault.getAbstractFileByPath(destination);
    return {
      file,
      folder,
      destination,
      collision: Boolean(existing && existing !== file),
    };
  }

  async previewInbox() {
    const notes = this.directInboxNotes();
    const plans = notes.map((file) => this.planFor(file));
    const resolvable = plans.filter((plan) => plan.folder).length;
    const collisions = plans.filter((plan) => plan.collision).length;
    const unresolved = notes.length - resolvable;
    new Notice(
      `Inbox preview: ${notes.length} note(s), ${resolvable} movable, ` +
        `${unresolved} unresolved, ${collisions} collision(s).`
    );
  }

  schedule(path, reading) {
    const previous = this.pending.get(path);
    if (previous) window.clearTimeout(previous);
    const timer = window.setTimeout(() => {
      this.pending.delete(path);
      void this.moveFromReading(path, reading, false);
    }, this.settings.debounceMs);
    this.pending.set(path, timer);
  }

  async sortCurrentNote() {
    const file = this.app.workspace.getActiveFile();
    if (!file || !this.isManagedPath(file.path)) {
      new Notice("The current note is outside the configured vocabulary paths.");
      return;
    }
    const reading = this.readingFor(file);
    if (!reading) {
      new Notice(`Add the ${this.settings.readingProperty} property first.`);
      return;
    }
    await this.moveFromReading(file.path, reading, true);
  }

  async sortInbox(showSummary) {
    const notes = this.directInboxNotes();
    let moved = 0;
    for (const file of notes) {
      const reading = this.readingFor(file);
      if (!reading) continue;
      if (await this.moveFromReading(file.path, reading, false)) moved += 1;
    }
    if (showSummary) new Notice(`Sorted ${moved} vocabulary note(s).`);
  }

  async ensureFolder(path) {
    const parts = cleanVaultPath(path).split("/").filter(Boolean);
    let current = "";
    for (const part of parts) {
      current = current ? `${current}/${part}` : part;
      const normalized = normalizePath(current);
      const existing = this.app.vault.getAbstractFileByPath(normalized);
      if (existing && !(existing instanceof TFolder)) {
        throw new Error(`A file blocks the destination folder: ${normalized}`);
      }
      if (!existing) await this.app.vault.createFolder(normalized);
    }
  }

  async moveFromReading(path, reading, showSuccess) {
    const normalizedPath = cleanVaultPath(path);
    if (!normalizedPath || this.moving.has(normalizedPath)) return false;
    const file = this.app.vault.getAbstractFileByPath(normalizedPath);
    if (!(file instanceof TFile) || !this.isManagedPath(file.path)) return false;

    const plan = this.planFor(file, reading);
    if (!plan.folder) {
      if (showSuccess) new Notice(`No gojūon folder found for: ${file.basename}`);
      return false;
    }
    if (plan.destination === file.path) {
      if (showSuccess) new Notice(`Already filed under ${plan.folder}.`);
      return false;
    }
    if (plan.collision) {
      new Notice(`Not moved; destination already exists: ${plan.destination}`);
      return false;
    }

    this.moving.add(normalizedPath);
    try {
      await this.ensureFolder(`${this.settings.wordRoot}/${plan.folder}`);
      await this.app.fileManager.renameFile(file, plan.destination);
      if (showSuccess) new Notice(`Moved to ${plan.folder}.`);
      return true;
    } catch (error) {
      console.error("Kotoba Vault", error);
      new Notice(`Could not move ${file.basename}.`);
      return false;
    } finally {
      this.moving.delete(normalizedPath);
    }
  }
};
