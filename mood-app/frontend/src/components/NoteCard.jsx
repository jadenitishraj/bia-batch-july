// One note shown as a card: its mood emoji, title, a preview of the text, tags and category.

export default function NoteCard({ note, onOpen, onDelete }) {
  return (
    <article
      className="note-card"
      style={{ "--note-color": note.category?.color || "#cbd5e1" }}
      onClick={onOpen}
    >
      <div className="note-top">
        <span className="note-mood" title={note.mood?.name}>
          {note.mood?.emoji || "📝"}
        </span>
        <button
          className="icon-btn"
          title="Delete note"
          onClick={(event) => {
            event.stopPropagation();
            onDelete();
          }}
        >
          🗑
        </button>
      </div>

      <h3 className="note-title">{note.title}</h3>
      <p className="note-text">{note.content}</p>

      <div className="note-tags">
        {note.tags.map((tag) => (
          <span className="tag" key={tag.id} style={{ "--chip-color": tag.color }}>
            #{tag.name}
          </span>
        ))}
      </div>

      <footer className="note-foot">
        {note.category && <span className="cat-pill">{note.category.name}</span>}
        <time>{new Date(note.updated_at).toLocaleDateString()}</time>
      </footer>
    </article>
  );
}
