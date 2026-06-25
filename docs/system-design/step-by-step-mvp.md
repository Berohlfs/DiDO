# Step by step (MVP)

1. [[CANCELLED - SINGLEPLAYER]] Deployed Hermes on Railway [here](https://github.com/praveen-ks-2001/hermes-agent-template).
2. Init Supabase project
3. Add pgvector extension to db (public schema)
4. Installed bun: `curl -fsSL https://bun.sh/install | bash`

## Install Bun

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

```
gbrain sources add shared --path "/Users/berohlfs/Documents/GitHub/DiDO-knowledge-base" --name "Sierra shared wiki"
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