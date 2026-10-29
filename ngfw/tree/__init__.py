"""ngtree / ngfw.tree — a tree you change right in the tree view, as one NiceGUI element for any page.

    from ngfw.tree import TreeEditor, JsonFileStore, MemoryStore        # in ngfw 0.4+
    from ngtree import TreeEditor, JsonFileStore, MemoryStore           # the standalone package

    TreeEditor(JsonFileStore('data/org.json'))                        # a file: live updates, undo, backups
    TreeEditor(MemoryStore(nodes, on_change=save), editable=False)    # your own data, read-only

The same code is in ngfw (0.4+) as ngfw.tree — `from ngfw.tree import TreeEditor, ...`.
"""
from . import ops
from .editor import FEATURES, TreeEditor
from .i18n import EN, translate
from .ops import TreeError
from .stores import JsonFileStore, MemoryStore, TreeStore

__all__ = ["TreeEditor", "TreeStore", "JsonFileStore", "MemoryStore", "TreeError", "FEATURES", "ops",
           "translate", "EN"]

__version__ = "0.1.0"
