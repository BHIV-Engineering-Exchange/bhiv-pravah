# Asset Transfer Report

## Repositories

- Current repository: `https://github.com/blackholeinfiverse80-creator/core-integrator-collaborative-.git`

## Branches

- Current branch: `main`
- No branch-specific work is documented in this handover.

## Environments

### Local
- default local ports: `8000`, `8001`, `8003`, `8004`, `8005`
- local database path: `db/context.db`
- local artifact path: `bhiv_bucket/`
- local telemetry path: `db/creator_core_telemetry/`

### Deployment targets
- Vercel: configuration file `vercel.json`
- Render: configuration file `render.yaml`
- Remote deployment docs: `RENDER_DEPLOYMENT.md`, `VERCEL_DEPLOYMENT.md`

## Credentials ownership locations (not actual secrets)

- Environment variables in `.env` and `.env.*` files
- Vercel deployment secrets should be managed in the Vercel project dashboard
- Render deployment secrets should be managed in the Render dashboard
- Local secret keys are expected in `.env` or service-specific env files

## Deployment ownership

- Local deployment: repository maintainer / team operator
- Creator Core deployment: repository maintainer / team operator
- BHIV Core deployment: repository maintainer / team operator
- Bucket deployment: repository maintainer / team operator
- Integration Bridge deployment: repository maintainer / team operator

## Testing ownership

- Health checks: `test_services.py`
- End-to-end validation: `full_tantra_flow_test.py`
- Creator Core tests: `creator-core/Core-Integrator-Sprint-1.1/tests`
- Operational testing: `deploy_and_test.py`

## Documentation ownership

- `README.md` — system overview and quick start
- `HANDOVER_EXECUTIVE_SUMMARY.md` — executive summary
- `SYSTEM_ARCHITECTURE_GUIDE.md` — architecture reference
- `REPOSITORY_MAP.md` — codebase navigation
- `RUNTIME_EXECUTION_FLOW.md` — runtime flow documentation
- `DEPLOYMENT_GUIDE.md` — deployment instructions
- `REPLAY_RECONSTRUCTION_GUIDE.md` — replay and reconstruction guide
- `TESTING_GUIDE.md` — testing and validation guide
- `FAQ.md` — full FAQ
- `OPEN_WORK_REGISTER.md` — open work register
- `KNOWLEDGE_TRANSFER_MINUTES.md` — knowledge transfer summary
- `review_packets/full_handover_packet_v1.md` — final review packet

## Pending reviews

- review of Prompt Runner implementation
- review of CET/Sarathi/Gate production design
- review of replay proof and distributed replay architecture
- review of remote deployment configuration

## Pending integrations

- Real Prompt Runner service integration
- TTG/TTV/Gurukul runtime integration
- Distributed replay validation nodes
- Noopur and video service integration guards

## Pending validations

- full end-to-end remote deployment validation
- distributed replay validation
- bucket and artifact consistency verification
- schema validation for artifacts

## Pending audits

- architectural audit of service boundaries
- replay audit proof generation
- constitutional audit of contract and authority stages

## Notes

This report is a transfer package for operational and engineering ownership. It contains the current repository state, deployment responsibilities, and documentation ownership.
