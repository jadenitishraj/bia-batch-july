// The left column: a search box plus filter chips for moods, categories and tags.
// Clicking a chip filters the notes; clicking it again clears the filter.

import { Chip, Section } from "./ui";

export default function Sidebar({ app, onManage }) {
  const { moods, categories, tags, filters, toggleFilter, setSearch } = app;

  return (
    <aside className="sidebar">
      <h1 className="logo">
        <span className="logo-dot">🌙</span> Moodnotes
      </h1>

      <input
        className="search"
        placeholder="Search your notes…"
        value={filters.search || ""}
        onChange={(event) => setSearch(event.target.value)}
      />

      <Section title="Moods" onManage={() => onManage("moods")}>
        {moods.map((mood) => (
          <Chip
            key={mood.id}
            color={mood.color}
            active={filters.mood_id === mood.id}
            onClick={() => toggleFilter("mood_id", mood.id)}
          >
            {mood.emoji} {mood.name}
          </Chip>
        ))}
      </Section>

      <Section title="Categories" onManage={() => onManage("categories")}>
        {categories.map((category) => (
          <Chip
            key={category.id}
            color={category.color}
            active={filters.category_id === category.id}
            onClick={() => toggleFilter("category_id", category.id)}
          >
            {category.name}
          </Chip>
        ))}
      </Section>

      <Section title="Tags" onManage={() => onManage("tags")}>
        {tags.map((tag) => (
          <Chip
            key={tag.id}
            color={tag.color}
            active={filters.tag_id === tag.id}
            onClick={() => toggleFilter("tag_id", tag.id)}
          >
            #{tag.name}
          </Chip>
        ))}
      </Section>
    </aside>
  );
}
