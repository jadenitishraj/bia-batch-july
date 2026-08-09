// Holds all the app's data in one place: notes, categories, tags, moods and the filters.
// Every component reads from here, so there is only one source of truth.

import { useCallback, useEffect, useState } from "react";

import { api } from "./api";

export function useNotesApp() {
  const [notes, setNotes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [tags, setTags] = useState([]);
  const [moods, setMoods] = useState([]);
  const [filters, setFilters] = useState({});

  // Load the three small lists used by the sidebar and the note editor
  const loadLists = useCallback(async () => {
    setCategories(await api.list("categories"));
    setTags(await api.list("tags"));
    setMoods(await api.list("moods"));
  }, []);

  const loadNotes = useCallback(async () => {
    setNotes(await api.list("notes", filters));
  }, [filters]);

  useEffect(() => {
    loadLists();
  }, [loadLists]);

  useEffect(() => {
    loadNotes();
  }, [loadNotes]);

  // Called after any change (including changes the chatbot makes) to refresh the screen
  const refresh = useCallback(async () => {
    await loadLists();
    await loadNotes();
  }, [loadLists, loadNotes]);

  // Click a filter chip to turn it on, click the same one again to turn it off
  const toggleFilter = (key, value) =>
    setFilters((current) => ({ ...current, [key]: current[key] === value ? undefined : value }));

  const setSearch = (value) => setFilters((current) => ({ ...current, search: value }));

  return { notes, categories, tags, moods, filters, toggleFilter, setSearch, refresh };
}
