// Small building blocks used all over the app: a coloured chip, a titled section, a popup.

export function Chip({ color, active, onClick, children }) {
  return (
    <button
      className={active ? "chip chip-active" : "chip"}
      style={{ "--chip-color": color }}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export function Section({ title, onManage, children }) {
  return (
    <section className="section">
      <header className="section-head">
        <span>{title}</span>
        <button className="manage-btn" onClick={onManage} title={`Manage ${title}`}>
          Manage
        </button>
      </header>
      <div className="chips">{children}</div>
    </section>
  );
}

export function Modal({ title, onClose, wide, children }) {
  return (
    <div className="overlay" onClick={onClose}>
      {/* stopPropagation keeps the popup open when you click inside it */}
      <div className={wide ? "modal modal-wide" : "modal"} onClick={(event) => event.stopPropagation()}>
        <header className="modal-head">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose}>
            ✕
          </button>
        </header>
        {children}
      </div>
    </div>
  );
}
