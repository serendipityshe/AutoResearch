# PaperBanana Skill Bootstrap Design

Date: 2026-03-29

## Goal

Adjust the published `paperbanana-0.1.0` skill so it works as a reusable skill package under `.claude` / `.codex` for arbitrary experiment projects running on local or remote servers.

The skill must no longer assume that a full `PaperBanana` source tree already exists beside the skill package. Instead, when the skill is invoked from an experiment project, it should bootstrap the upstream repository into that project if needed, then run PaperBanana from the checked-out project-local repository.

## Current Problem

The current skill package contains a `run.py` implementation that imports `agents`, `utils`, `configs`, and `data` as if the complete upstream repository already exists locally. In the packaged skill directory, those modules are absent, so the packaged `run.py` is not a reliable execution entrypoint on its own.

For the user's actual workflow, the effective entrypoint is the skill instructions in `paperbanana-0.1.0/SKILL.md`, which are consumed by the agent runtime and used to decide what to run. Therefore the behavior change should be implemented in `SKILL.md`, not by relying on the packaged `run.py`.

## Recommended Approach

Use project-local bootstrap behavior in `paperbanana-0.1.0/SKILL.md`.

### Repository placement

- Treat the current working directory as the experiment project root.
- Use a fixed repository path at `./PaperBanana`.
- If `./PaperBanana/.git` exists, reuse it as-is.
- If `./PaperBanana/.git` does not exist, clone `https://github.com/dwzhu-pku/PaperBanana.git` into `./PaperBanana`.

### Update policy

- Do not run `git pull` automatically.
- Do not replace an existing `./PaperBanana` checkout.
- This preserves reproducibility across remote experiments and avoids modifying a repo the user may already have pinned or edited.

### Execution model

- `SKILL.md` should instruct the agent to bootstrap `./PaperBanana` before any PaperBanana execution.
- After bootstrap, all runtime commands should target files inside `./PaperBanana/`, not the packaged skill directory.
- The packaged `paperbanana-0.1.0/run.py` should not be described as the primary runtime path.

### Output contract

- The skill should still be documented as producing final image files.
- The user-facing result should be the saved output image path or paths.
- If multiple candidates are generated, the skill should report multiple image paths.

## User-Facing Flow

1. User invokes the `paperbanana` skill from an experiment project.
2. The skill checks whether `./PaperBanana/.git` exists.
3. If absent, the skill clones the upstream repository into `./PaperBanana`.
4. The skill runs the PaperBanana workflow from `./PaperBanana`.
5. PaperBanana saves final image files and reports their paths.

## SKILL.md Changes

Update `paperbanana-0.1.0/SKILL.md` in these areas:

- Rewrite setup instructions so they describe bootstrap behavior from an arbitrary project directory.
- Remove wording that assumes the user has already entered a complete PaperBanana repository root before invoking the skill.
- Replace references to packaged skill-local execution with project-local `./PaperBanana/...` execution.
- Add an explicit note that clone happens only when `./PaperBanana` is missing.
- Add an explicit note that existing `./PaperBanana` checkouts are reused without auto-updating.
- Clarify that the end result is the final generated image file path or paths.

## Error Handling

- If clone fails, the skill should surface the clone command and failure clearly instead of silently falling back.
- If the expected upstream entrypoint is missing after clone, the skill should report that the cloned repository layout does not match the documented invocation path.
- If required API credentials are missing, the skill should instruct the user which environment variables or config file entries are required.

## Testing Strategy

- Review the updated `SKILL.md` to confirm it no longer assumes local packaged Python modules are executable.
- Validate the documented bootstrap path against the current upstream repository layout before finalizing command examples.
- Confirm the documented behavior matches the intended server workflow:
  - fresh project with no `./PaperBanana`
  - existing project with a reusable `./PaperBanana`
  - multi-candidate output reporting

## Non-Goals

- Rewriting the upstream `PaperBanana` project itself.
- Making the packaged `paperbanana-0.1.0/run.py` independently functional.
- Adding automatic repository updates or version pinning in this change.

## Open Item Before Implementation

Before editing `SKILL.md`, verify the concrete upstream entrypoint path inside the cloned `PaperBanana` repository so the documented commands point at the correct file.
