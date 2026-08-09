// The whole screen: filters on the left, notes in the middle, chatbot on the right.

import { useState } from "react";

import Chat from "./components/Chat";
import ManagePanel from "./components/ManagePanel";
import NoteEditor from "./components/NoteEditor";
import NoteGrid from "./components/NoteGrid";
import Sidebar from "./components/Sidebar";
import { useNotesApp } from "./useNotesApp";

export default function App() {
  const app = useNotesApp();
  const [editing, setEditing] = useState(null); // the note being written, or null
  const [managing, setManaging] = useState(null); // "categories" | "tags" | "moods" | null

  return (
    <div className="app">
      <Sidebar app={app} onManage={setManaging} />
      <NoteGrid app={app} onOpen={setEditing} />
      <Chat onChanged={app.refresh} />

      {editing && <NoteEditor note={editing} app={app} onClose={() => setEditing(null)} />}
      {managing && <ManagePanel kind={managing} app={app} onClose={() => setManaging(null)} />}
    </div>
  );
}
