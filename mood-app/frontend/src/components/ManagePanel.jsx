// One popup that can add, rename, recolour and delete categories, tags or moods.
// They all behave the same, so we describe the differences in SETTINGS and reuse the rest.

import { useState } from "react";

import { api } from "../api";
import { Modal } from "./ui";

const SETTINGS = {
  categories: { title: "Categories", one: "category", blank: { name: "", color: "#cc785c" } },
  tags: { title: "Tags", one: "tag", blank: { name: "", color: "#a38a5c" } },
  moods: { title: "Moods", one: "mood", blank: { name: "", emoji: "🙂", color: "#d97757" } },
};

export default function ManagePanel({ kind, app, onClose }) {
  const { title, one, blank } = SETTINGS[kind];
  const items = app[kind];
  const [draft, setDraft] = useState(blank);

  async function addItem() {
    if (!draft.name.trim()) return;
    await api.create(kind, draft);
    setDraft(blank);
    app.refresh();
  }

  async function saveItem(item, changes) {
    await api.update(kind, item.id, { ...item, ...changes });
    app.refresh();
  }

  async function removeItem(item) {
    await api.remove(kind, item.id);
    app.refresh();
  }

  return (
    <Modal title={`Manage ${title}`} onClose={onClose}>
      <div className="rows">
        {items.map((item) => (
          <div className="row" key={item.id}>
            {"emoji" in blank && (
              <input
                className="row-emoji"
                defaultValue={item.emoji}
                onBlur={(event) => saveItem(item, { emoji: event.target.value })}
              />
            )}
            <input
              className="row-input"
              defaultValue={item.name}
              onBlur={(event) => saveItem(item, { name: event.target.value })}
            />
            <input
              type="color"
              className="row-color"
              defaultValue={item.color}
              onBlur={(event) => saveItem(item, { color: event.target.value })}
            />
            <button className="icon-btn" title="Delete" onClick={() => removeItem(item)}>
              🗑
            </button>
          </div>
        ))}
      </div>

      <div className="row row-new">
        {"emoji" in blank && (
          <input
            className="row-emoji"
            value={draft.emoji}
            onChange={(event) => setDraft({ ...draft, emoji: event.target.value })}
          />
        )}
        <input
          className="row-input"
          placeholder={`New ${one} name`}
          value={draft.name}
          onChange={(event) => setDraft({ ...draft, name: event.target.value })}
        />
        <input
          type="color"
          className="row-color"
          value={draft.color}
          onChange={(event) => setDraft({ ...draft, color: event.target.value })}
        />
        <button className="primary small" onClick={addItem}>
          Add
        </button>
      </div>

      <p className="hint">Changes save when you click away from a box.</p>
    </Modal>
  );
}
