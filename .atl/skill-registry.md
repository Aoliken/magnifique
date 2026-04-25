# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| /graphify | graphify | /home/s/.config/opencode/skills/graphify/SKILL.md |
| When user says "judgment day", "judgment-day", "review adversarial", "dual review", "doble review", "juzgar", "que lo juzguen". | judgment-day | /home/s/.config/opencode/skills/judgment-day/SKILL.md |
| When creating a GitHub issue, reporting a bug, or requesting a feature. | issue-creation | /home/s/.config/opencode/skills/issue-creation/SKILL.md |
| When creating a pull request, opening a PR, or preparing changes for review. | branch-pr | /home/s/.config/opencode/skills/branch-pr/SKILL.md |
| When user asks to create a new skill, add agent instructions, or document patterns for AI. | skill-creator | /home/s/.config/opencode/skills/skill-creator/SKILL.md |
| When writing Go tests, using teatest, or adding test coverage. | go-testing | /home/s/.config/opencode/skills/go-testing/SKILL.md |

## Compact Rules

### graphify
- Default to `.` when no path is provided; do not ask for one.
- Ensure graphify is installed first and persist the interpreter in `graphify-out/.graphify_python`.
- Run detection before extraction; stop if no supported files exist.
- If corpus is too large, warn and ask for a narrower subfolder before proceeding.
- Run AST extraction for code in parallel with semantic extraction for non-code.
- Preserve an honest audit trail: distinguish extracted, inferred, and ambiguous edges.

### judgment-day
- Use the skill registry first and inject matching compact rules into BOTH judge prompts and the fix prompt.
- Launch exactly two independent blind judges in parallel; never review sequentially.
- Treat findings confirmed by both judges as highest confidence.
- Fix confirmed CRITICAL and real WARNING issues, then re-judge; theoretical warnings become INFO.
- After two fix iterations, escalate to the user instead of looping forever.

### issue-creation
- Never create blank issues; always use the bug or feature template.
- Search for duplicates before opening a new issue.
- New issues must carry `status:needs-review`; PR work waits for `status:approved`.
- Questions belong in Discussions, not Issues.
- Fill every required template field and include reproduction details for bugs.

### branch-pr
- Every PR MUST link one approved issue; no issue, no PR.
- Branch names must follow `type/description` with lowercase `a-z0-9._-`.
- PRs need exactly one `type:*` label and must use the PR template.
- Use conventional commits only; never add AI attribution trailers.
- Run required validation tooling before opening the PR.

### skill-creator
- Create a skill only for reusable, non-trivial patterns; otherwise prefer regular docs.
- Use `skills/{skill-name}/SKILL.md` as the core structure and keep references local.
- Frontmatter must include name, description with trigger, Apache-2.0 license, author, and version.
- Put critical patterns first, keep examples minimal, and avoid fluffy explanations.
- Add the new skill to AGENTS.md after creation.

### go-testing
- Prefer table-driven tests for Go logic with multiple cases.
- Test Bubbletea state transitions by calling `Update()` directly.
- Use `teatest.NewTestModel()` for interactive TUI flows.
- Use golden files for stable view/output assertions.
- Cover both success and error paths, and isolate filesystem work with `t.TempDir()`.

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| AGENTS.md | /home/s/Insync/sergio@eim.esc.edu.ar/Google Drive/Mochila/Bunker4/magnifique/AGENTS.md | Project architecture and data model reference |

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted — no need to read index files to discover more.
