// The popup for writing or editing a note: title, text, mood, category and tags.

import { useState } from "react";

import { api } from "../api";
import { Chip, Modal } from "./ui";

export default function NoteEditor({ note, app, onClose }) {
  const { categories, moods, tags, refresh } = app;

  const [form, setForm] = useState({
    title: note.title || "",
    content: note.content || "",
    category_id: note.category?.id || "",
    mood_id: note.mood?.id || "",
    tag_ids: (note.tags || []).map((tag) => tag.id),
  });

  const change = (key, value) => setForm({ ...form, [key]: value });

  const toggleTag = (id) =>
    change("tag_ids", form.tag_ids.includes(id) ? form.tag_ids.filter((x) => x !== id) : [...form.tag_ids, id]);

  async function save() {
    if (!form.title.trim()) return;
    const body = { ...form, category_id: form.category_id || null, mood_id: form.mood_id || null };
    if (note.id) await api.update("notes", note.id, body);
    else await api.create("notes", body);
    await refresh();
    onClose();
  }

  return (
    <Modal title={note.id ? "Edit note" : "New note"} onClose={onClose}>
      <input
        className="field"
        placeholder="Give it a title…"
        value={form.title}
        onChange={(event) => change("title", event.target.value)}
      />
      <textarea
        className="field area"
        placeholder="What is on your mind?"
        value={form.content}
        onChange={(event) => change("content", event.target.value)}
      />

      <label className="label">Mood</label>
      <div className="chips">
        {moods.map((mood) => (
          <Chip
            key={mood.id}
            color={mood.color}
            active={form.mood_id === mood.id}
            onClick={() => change("mood_id", form.mood_id === mood.id ? "" : mood.id)}
          >
            {mood.emoji} {mood.name}
          </Chip>
        ))}
      </div>

      <label className="label">Category</label>
      <div className="chips">
        {categories.map((category) => (
          <Chip
            key={category.id}
            color={category.color}
            active={form.category_id === category.id}
            onClick={() => change("category_id", form.category_id === category.id ? "" : category.id)}
          >
            {category.name}
          </Chip>
        ))}
      </div>

      <label className="label">Tags</label>
      <div className="chips">
        {tags.map((tag) => (
          <Chip
            key={tag.id}
            color={tag.color}
            active={form.tag_ids.includes(tag.id)}
            onClick={() => toggleTag(tag.id)}
          >
            #{tag.name}
          </Chip>
        ))}
      </div>

      <div className="modal-foot">
        <button className="ghost" onClick={onClose}>
          Cancel
        </button>
        <button className="primary" onClick={save}>
          Save note
        </button>
      </div>
    </Modal>
  );
}
