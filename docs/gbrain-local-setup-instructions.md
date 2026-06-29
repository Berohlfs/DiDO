# Local setup - Step by step instructions

1. [[CANCELLED - SINGLEPLAYER]] Deployed Hermes on Railway [here](https://github.com/praveen-ks-2001/hermes-agent-template).
2. Init Supabase project
3. Add pgvector extension to db (public schema)
4. Issued Anthropic and OpenAI API keys

## Install Bun and GBrain deps

```
curl -fsSL https://bun.sh/install | bash

echo 'export BUN_INSTALL="$HOME/.bun"' >> ~/.zshrc
echo 'export PATH="$BUN_INSTALL/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

bun --version
which bun
```

```
cd /Users/berohlfs/Documents/GitHub/dido/gbrain
bun install
bun link

gbrain --version    # should print 0.42.53.0 — proof it's your fork, not upstream
which gbrain        # should resolve to ~/.bun/bin/gbrain → this repo
```

## Init GBrain with API keys and Supabase

```
export OPENAI_API_KEY="sk-proj-your-key-here"
export ANTHROPIC_API_KEY="sk-proj-your-key-here"
gbrain init --supabase
[[PASTE THE SUPABASE CONNECTION STRING]]
gbrain doctor
```

## Sync with external knowledge repo

- Generate SSH keypair (ssh-keygen)
- Register it on `https://github.com/settings/keys`

```
# (host trust — not auth)
ssh-keyscan -t ed25519,rsa github.com >> ~/.ssh/known_hosts
sort -u ~/.ssh/known_hosts -o ~/.ssh/known_hosts
chmod 600 ~/.ssh/known_hosts

# (the only thing that touched git)
git -C ~/Documents/GitHub/DiDO-knowledge-base remote set-url origin git@github.com:Berohlfs/DiDO-knowledge-base.git
```

```
gbrain sources add shared --path "/Users/berohlfs/Documents/GitHub/DiDO-knowledge-base" --name "Sierra shared wiki"
gbrain sources list
gbrain sync --all
gbrain embed --stale
```

## Health/Status commands

```
gbrain sources status  # shows the source + page count + sync time
gbrain stats  # page / chunk / embedding counts
gbrain doctor   
gbrain think "what's the latest with acme-co?"

gbrain models
gbrain config show
```

## Run the MCP server locally and expose it with Ngrok

```
ngrok http 3131
export GBRAIN_HTTP_CORS_ORIGIN="https://untrue-lividly-undermine.ngrok-free.dev"
gbrain serve --http --port 3131 --bind 0.0.0.0 --public-url https://untrue-lividly-undermine.ngrok-free.dev

[[GET admin token]]
```

## Create an OAuth user

```
gbrain auth register-client bernardo \
  --scopes "read write" \
  --source shared \
  --federated-read shared \
  --redirect-uri https://claude.ai/api/mcp/auth_callback \
  --redirect-uri https://claude.com/api/mcp/auth_callback \
  --grant-types authorization_code,refresh_token,client_credentials

[[GET client secret and client id]]
```

## Add the MCP to Claude Cowork

- Open Claude Desktop
- Go to Settings → Connectors
- Select Add custom connector
- Enter the remote MCP server URL
- Open Advanced settings
- Enter the OAuth Client ID and Client Secret
- Add the connector, then click Connect to complete OAuth authorization.

## CRONS

- `gbrain dream`
- `gbrain sync --all` and `gbrain embed --stale`

## Dreaming

- Enable enrichment

```
# Flesh out thin/stub pages from what the brain already knows (1 LLM call/page)
gbrain config set cycle.enrich_thin.enabled true
gbrain config set cycle.enrich_thin.max_pages_per_tick 3
gbrain config set cycle.enrich_thin.max_cost_usd 0.50          # per-source cap
gbrain config set cycle.enrich_thin.max_total_cost_usd 3       # brain-wide per cycle
gbrain config set cycle.enrich_thin.workers 1                  # hard budget ceiling
gbrain config set cycle.enrich_thin.model claude-haiku-4-5     # cheap model for enrichment

# Extract facts from ingested conversations/transcripts
gbrain config set cycle.conversation_facts_backfill.enabled true
gbrain config set cycle.conversation_facts_backfill.max_total_cost_usd 3

# Optimize brain-resident skills
gbrain config set cycle.skillopt.enabled true
gbrain config set cycle.skillopt.brain_wide_cap_usd 5
```

`gbrain dream --dir /Users/berohlfs/Documents/GitHub/DiDO-knowledge-base`