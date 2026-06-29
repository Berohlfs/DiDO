# DiDO

Sierra's company brain.

## About GBrain

- Compounded knowledge anotations (file system - single player | git - multiplayer)
- Supabase (indexing, vectorizing, soft deletes)
- Built-in OAuth

## MCP 

- Put, List, Delete tools. Updates both file system and postgreSQL.

## Database

1. Tables

- `pages`
     - Soft deletes

## Knowledge Repo

- `gbrain sync --all` pulls from remote
- `gbrain embbed --stale` content gets chunked, hashed, and embedded from your local working-tree files. The remote is never read for content.