# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from pathlib import Path


class Sandbox:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = Path(os.path.expandvars(workspace_dir)).expanduser()

    def list_files(self, prefix: str = "") -> list[str]:
        """Return relative file paths under workspace_dir/prefix, sorted."""
        root = self.workspace_dir.resolve()
        base = (self.workspace_dir / prefix).resolve() if prefix else root
        if base != root and root not in base.parents:
            return []
        if not base.exists():
            return []
        results = []
        for dirpath, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if not d.startswith("."))
            for f in sorted(files):
                if not f.startswith("."):
                    # Relative to `root`, not `self.workspace_dir`: os.walk()
                    # descends from the resolved `base`, so its dirpaths carry
                    # the resolved spelling.  Wherever the two differ — a
                    # symlinked workspace, macOS /tmp -> /private/tmp, a Windows
                    # 8.3 short path — relative_to(self.workspace_dir) raises
                    # ValueError.  They are identical when nothing is aliased.
                    rel = Path(dirpath, f).relative_to(root)
                    # The tool contract (and /workspace/<path> concatenation in
                    # the interpreter) requires "/" separators on every host.
                    results.append(rel.as_posix())
        return results

    def search_files(self, pattern: str) -> list[str]:
        """Return relative file paths matching a glob pattern."""
        # Reject any match that navigates via "..", even if it loops back into
        # the workspace.  We check the lexical path (p.parts), not p.resolve():
        # __reserved__init populates the workspace with symlinks to source
        # files for COW isolation, and resolving those would land outside
        # workspace_dir for every legitimate match.
        results = []
        for p in self.workspace_dir.glob(pattern):
            if not p.is_file() or p.name.startswith("."):
                continue
            if ".." in p.parts:
                continue
            results.append(p.relative_to(self.workspace_dir).as_posix())
        return sorted(results)
