# Graph Report - postits!  (2026-11-19)

## Corpus Check
- 4 files · ~1,558 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 1 file(s) not represented in the graph (top: .sqlite3 1)

## Summary
- 33 nodes · 45 edges · 7 communities (2 shown, 5 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `53a071d6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- connect
- User
- profile
- receipt
- AGENTS.md

## God Nodes (most connected - your core abstractions)
1. `connect()` - 8 edges
2. `apply()` - 5 edges
3. `User` - 5 edges
4. `receipt()` - 4 edges
5. `load_user()` - 4 edges
6. `login()` - 4 edges
7. `profile()` - 4 edges
8. `register()` - 3 edges
9. `logout()` - 3 edges
10. `graphify` - 1 edges

## Surprising Connections (you probably didn't know these)
- `load_user()` --calls--> `connect()`  [EXTRACTED]
  app.py → app.py  _Bridges community 1 → community 2_
- `profile()` --calls--> `connect()`  [EXTRACTED]
  app.py → app.py  _Bridges community 1 → community 3_
- `receipt()` --calls--> `connect()`  [EXTRACTED]
  app.py → app.py  _Bridges community 1 → community 4_

## Import Cycles
- None detected.

## Communities (7 total, 5 thin omitted)

### Community 1 - "connect"
Cohesion: 0.40
Nodes (3): apply(), connect(), register()

### Community 2 - "User"
Cohesion: 0.33
Nodes (3): load_user(), login(), User

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `app.py`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Why does `logout()` connect `profile` to `app.py`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `apply()` connect `connect` to `app.py`, `receipt`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._