// One numbered section inside the 👁 popup: a big number, a title, a short note, then content.

export default function Part({ number, title, note, children }) {
  return (
    <section className="part">
      <h3 className="part-head">
        <span className="part-num">{number}</span>
        {title}
      </h3>
      {note && <p className="part-note">{note}</p>}
      {children}
    </section>
  );
}
