# Deploy Praxis to Production

The repo is a three-package monorepo. The piece you deploy publicly is the
operator terminal at `app/`. The Python backtester (`agent/`) and the
contracts (`contracts/`) ship as code, not as services.

---

## 1 · GitHub

```bash
# from the repo root
git remote add origin git@github.com:Adi-gitX/Praxis.git
git push -u origin main
```

If `main` already exists on the remote and is non-empty, take the destructive
path only once and only with explicit intent:

```bash
git push -u --force-with-lease origin main
```

`--force-with-lease` refuses to overwrite if someone else pushed since you
last fetched, so it is safer than `--force`.

## 2 · Vercel (one-click)

The cleanest monorepo pattern is to point Vercel at the `app/` subdirectory.
Two minutes from cold:

1. **Import** the GitHub repo at <https://vercel.com/new>.
2. In the import wizard, set **Root Directory** to `app` (this is the only
   non-default setting).
3. Framework auto-detects as **Next.js**. Build command, install command and
   output directory all come from [`app/vercel.json`](../app/vercel.json).
4. **Deploy.** First build takes ~90s. The deployment URL appears at the top
   of the project dashboard.

The committed `app/vercel.json` ships sensible production headers
(`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, HSTS), an
edge-region pin (`iad1`), a long-cache rule on the OG image, and a 301 from
the legacy `/dashboard` path to `/terminal`.

### Optional environment variables

| Var | Used by | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | future paper-trade websocket | not required for the demo terminal — it renders deterministic seeded data when unset |
| `OPENAI_API_KEY` | `LLMMetaPolicy` (Python only) | server-side only; never expose to the browser |
| `WALLET_KEY` | `contracts/hardhat.config.ts` deploys | only needed when running `npx hardhat ignition deploy` |
| `ETHERSCAN_API_KEY` | `npx hardhat verify` on Base Sepolia | optional |

### Custom domain

Add the domain in **Project → Settings → Domains**. Vercel issues the TLS
certificate automatically. Update the OG image's host by setting
`metadataBase` in [`app/app/layout.tsx`](../app/app/layout.tsx) to the new
canonical URL.

## 3 · Contracts (Base Sepolia)

After connecting GitHub but before any live deployment, redeploy the
contracts under your own EOA so nothing carries over from any prior
attribution:

```bash
cd contracts
cp .env.example .env  # WALLET_KEY=0x... and ETHERSCAN_API_KEY=...
npm install
npx hardhat compile
npx hardhat ignition deploy ./ignition/modules/Praxis.ts \
    --network base-sepolia \
    --parameters '{"baseAsset":"0x036CbD53842c5426634e7929541eC2318f3dCF7e"}'
```

The `baseAsset` parameter is the USDC address on Base Sepolia. Replace with
the mainnet USDC for production. Print the four resulting contract
addresses and add them to `app/lib/contracts.ts` for the `/vault` page.

## 4 · Backtester service (optional)

If you want the operator terminal to read live decisions from the Python
backtester instead of the seeded demo data, run the agent as a service:

```bash
cd agent
poetry install
poetry run uvicorn praxis.server:app --host 0.0.0.0 --port 8000
```

(The `praxis.server` FastAPI module is scaffolded for this; live wiring is
on the roadmap.) Set `NEXT_PUBLIC_API_URL=http://your-host:8000` in Vercel.

## 5 · CI (recommended next step)

A minimal GitHub Actions workflow that runs the same five tooling checks on
every PR:

```yaml
# .github/workflows/ci.yml
name: ci
on: [push, pull_request]
jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install poetry
      - run: cd agent && poetry install
      - run: cd agent && poetry run pytest -q
      - run: cd agent && poetry run mypy --strict src/praxis
      - run: cd agent && poetry run ruff check .

  node:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd app && npm ci && npm run build
      - run: cd contracts && npm ci && WALLET_KEY=0x0000000000000000000000000000000000000000000000000000000000000001 npx hardhat test
```

Drop this in `.github/workflows/ci.yml` once CI is desired.

## Verification before announcing

```bash
# fresh clone + reproduce the headline
git clone <your-fork>
cd <repo>
cd agent && poetry install && poetry run pytest -q
poetry run jupyter nbconvert --execute --to notebook --inplace \
    ../research/H05_hmm_volatility_regime.ipynb
cd ../app && npm install && npm run build
cd ../contracts && WALLET_KEY=0x...01 npx hardhat test
```

If any step fails on a fresh clone, do not announce the URL.
