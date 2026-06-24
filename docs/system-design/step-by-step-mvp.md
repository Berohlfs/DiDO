# Step by step (MVP)

1. [[CANCELLED - SINGLEPLAYER]] Deployed Hermes on Railway [here](https://github.com/praveen-ks-2001/hermes-agent-template).
2. Init Supabase project
3. Add pgvector extension to db (public schema)
4. Installed bun: `curl -fsSL https://bun.sh/install | bash`

```
cd /Users/berohlfs/Documents/GitHub/dido/gbrain
bun install
bun link

gbrain --version    # should print 0.42.53.0 — proof it's your fork, not upstream
which gbrain        # should resolve to ~/.bun/bin/gbrain → this repo
```

```
export OPENAI_API_KEY="sk-proj-your-key-here"
gbrain init --supabase
[[PASTE THE SUPABASE CONNECTION STRING]]
gbrain doctor
```

