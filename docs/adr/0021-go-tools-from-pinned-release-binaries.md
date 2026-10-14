# Go tools come from pinned upstream release binaries, not `go install`

The backend image ships four Go binaries: subfinder, httpx (as `httpx-probe`), amass and
amass's `ae_isready`. Compiling all four from source was the slowest stage of a cold image
build (~2 min on an arm64 laptop, and it runs on every cold-cache CI/release build).

## Decision

`backend/Dockerfile`'s `go-tools-fetch` stage downloads subfinder, httpx and amass from their
GitHub release archives, pinned by exact tag **and** a per-arch sha256 (`TARGETARCH`, amd64/arm64,
taken from each release's checksums file). A hash mismatch fails the build.

- **Same binaries, less work.** The release builds are static and already stripped, the same size
  as a `-s -w` source build, and the same pinned versions. A cold Go stage drops from ~127 s to
  ~36 s, since the download runs in parallel with the one remaining source build.
- **`ae_isready` is still `go install`ed.** amass's release archive doesn't include it, and
  replacing it with an in-app readiness probe would mean changing `amass_engine_service.py` to save
  ~30 s of cold build time.
- **Cost.** Bumping a tool means updating its version and both arch hashes together, instead of
  one tag. Dependabot doesn't track either form, so manual bumps were already the norm.
- **Trust.** We already trusted these upstreams' source at a pinned tag. Trusting their CI-built
  artifact at a pinned hash only adds their release pipeline, and the hash pin prevents the artifact
  from being silently swapped.
