from __future__ import annotations
from .db import connect
LEVELS={"claimed","inferred","build_verified","test_verified","benchmarked"}

def add_capability(repository_id: int, name: str, description: str | None = None,
                   evidence_level: str = "claimed", evidence: str | None = None) -> int:
    if evidence_level not in LEVELS:
        raise ValueError(f"Invalid evidence level. Choose: {', '.join(sorted(LEVELS))}")
    with connect() as conn:
        if not conn.execute("SELECT id FROM repositories WHERE id=?",(repository_id,)).fetchone():
            raise ValueError(f"Repository {repository_id} does not exist")
        cur=conn.execute("""INSERT INTO capabilities
          (repository_id,name,description,evidence_level,evidence) VALUES (?,?,?,?,?)""",
          (repository_id,name,description,evidence_level,evidence))
        return int(cur.lastrowid)

def list_capabilities():
    with connect() as conn:
        return conn.execute("""SELECT c.id,c.repository_id,r.owner,r.name AS repository,
          c.name,c.evidence_level,c.evidence FROM capabilities c
          JOIN repositories r ON r.id=c.repository_id ORDER BY c.id""").fetchall()
