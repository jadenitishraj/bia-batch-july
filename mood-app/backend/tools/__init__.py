# Collects every tool into one list, so the agent can be handed all of them at once.

from tools import category_tools, mood_tools, note_tools, tag_tools

ALL_TOOLS = [
    # notes
    note_tools.list_notes,
    note_tools.count_notes_by_mood,
    note_tools.create_note,
    note_tools.update_note,
    note_tools.delete_note,
    # categories
    category_tools.list_categories,
    category_tools.create_category,
    category_tools.update_category,
    category_tools.delete_category,
    # tags
    tag_tools.list_tags,
    tag_tools.create_tag,
    tag_tools.update_tag,
    tag_tools.delete_tag,
    # moods
    mood_tools.list_moods,
    mood_tools.create_mood,
    mood_tools.update_mood,
    mood_tools.delete_mood,
]
