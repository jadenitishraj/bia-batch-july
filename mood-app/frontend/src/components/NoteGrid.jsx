// The middle column: a "New note" button and all the note cards.

import { api } from "../api";
import NoteCard from "./NoteCard";

export default function NoteGrid({ app, onOpen }) {
  const { notes, refresh } = app;

  async function deleteNote(id) {
    await api.remove("notes", id);
    refresh();
  }

  return (
    <main className="main">
      <header className="main-head">
        <div>
          <h2>Your notes</h2>
          <p className="muted">{notes.length} notes</p>
        </div>
        <button className="primary" onClick={() => onOpen({})}>
          ＋ New note
        </button>
      </header>

      {notes.length === 0 ? (
        <p className="empty">Nothing here yet — write your first note ✨</p>
      ) : (
        <div className="grid">
          {notes.map((note) => (
            <NoteCard
              key={note.id}
              note={note}
              onOpen={() => onOpen(note)}
              onDelete={() => deleteNote(note.id)}
            />
          ))}
        </div>
      )}
    </main>
  );
}
