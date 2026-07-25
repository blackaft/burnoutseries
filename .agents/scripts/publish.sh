#!/usr/bin/env bash

set -Eeuo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Burnout Series — local knowledge-base publisher
# ─────────────────────────────────────────────────────────────────────────────

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

BASE_BRANCH="dev"
REMOTE="origin"
REPO=""
COMMIT_MESSAGE="chore: update Burnout Series knowledge base"

TEMP_DIR=""
UPDATE_BRANCH=""

info() {
  printf "\nℹ️  %s\n" "$1"
}

success() {
  printf "\n✅ %s\n" "$1"
}

warning() {
  printf "\n⚠️  %s\n" "$1"
}

fail() {
  printf "\n❌ %s\n\n" "$1" >&2
  exit 1
}

cleanup_temp() {
  if [[ -n "${TEMP_DIR:-}" && -d "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR"
  fi
}

trap cleanup_temp EXIT

confirm() {
  local prompt="$1"

  if [[ "${AUTO_APPROVE:-0}" == "1" ]]; then
    return 0
  fi

  printf "\n👉 %s [y/N] " "$prompt"
  read -r answer

  case "$answer" in
    y|Y|yes|YES)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. Check essential tools
# ─────────────────────────────────────────────────────────────────────────────

info "Checking the tools needed to publish the knowledge base..."

command_exists git || fail \
  "Git is not installed.

Install Git from:
https://git-scm.com/downloads

Then run:
  ./publish.sh"

success "Git is ready."

# ─────────────────────────────────────────────────────────────────────────────
# Check Python
# ─────────────────────────────────────────────────────────────────────────────

if ! command_exists python3; then
  fail "Python 3 was not found.

Install Python 3 from:
https://www.python.org/downloads/

Windows users:
During installation, enable “Add Python to PATH”.

Then close and reopen your terminal and run:
  ./publish.sh"
fi

PYTHON_VERSION="$(python3 --version 2>&1)"
success "Found ${PYTHON_VERSION}."

# Confirm that Python can create virtual environments.
if ! python3 -m venv --help >/dev/null 2>&1; then
  fail "Python is installed, but virtual-environment support is unavailable.

macOS:
  Install the latest Python from:
  https://www.python.org/downloads/

Ubuntu / Debian:
  sudo apt-get install python3-venv

Fedora:
  sudo dnf install python3

Windows:
  Reinstall Python from:
  https://www.python.org/downloads/

Then run:
  ./publish.sh"
fi

success "Python virtual environments are supported."

# ─────────────────────────────────────────────────────────────────────────────
# Check GitHub CLI
# ─────────────────────────────────────────────────────────────────────────────

if ! command_exists gh; then
  fail "GitHub CLI was not found.

Install it from:
https://cli.github.com/

Then close and reopen your terminal and run:
  gh auth login

After signing in, run:
  ./publish.sh"
fi

GH_VERSION="$(gh --version | head -n 1)"
success "Found ${GH_VERSION}."

# ─────────────────────────────────────────────────────────────────────────────
# Check GitHub authentication
# ─────────────────────────────────────────────────────────────────────────────

if ! gh auth status >/dev/null 2>&1; then
  fail "GitHub CLI is installed, but it is not signed in.

Run:
  gh auth login

Recommended choices:

  GitHub.com
  HTTPS
  Login with a web browser

After authentication completes, run:
  ./publish.sh"
fi

GITHUB_ACCOUNT="$(
  gh api user --jq '.login' 2>/dev/null || printf 'authenticated user'
)"

success "GitHub CLI is authenticated as ${GITHUB_ACCOUNT}."

REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"

success "Repository detected: ${REPO}."

# ─────────────────────────────────────────────────────────────────────────────
# 2. Confirm repository and starting branch
# ─────────────────────────────────────────────────────────────────────────────

info "Checking the repository..."

git rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
  fail "This script must be run from inside the Burnout Series repository."

git remote get-url "$REMOTE" >/dev/null 2>&1 ||
  fail "The '${REMOTE}' Git remote is not configured."

GIT_USER_NAME="$(git config user.name || true)"
GIT_USER_EMAIL="$(git config user.email || true)"

if [[ -z "$GIT_USER_NAME" ]]; then
  fail "Your Git username is not configured.

Set it with:

  git config user.name \"Your Name\"

Then run:

  ./publish.sh"
fi

if [[ -z "$GIT_USER_EMAIL" ]]; then
  fail "Your Git email is not configured.

Set it with:

  git config user.email \"you@example.com\"

Then run:

  ./publish.sh"
fi

USER_SLUG="$(
  printf '%s' "$GIT_USER_NAME" |
    tr '[:upper:]' '[:lower:]' |
    sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//'
)"

[[ -n "$USER_SLUG" ]] ||
  fail "A branch name could not be created from your Git username."

UPDATE_BRANCH="${USER_SLUG}-series-update"

CURRENT_BRANCH="$(git branch --show-current)"

if [[ "$CURRENT_BRANCH" != "$BASE_BRANCH" &&
      "$CURRENT_BRANCH" != "$UPDATE_BRANCH" ]]; then
  fail "You are currently on '${CURRENT_BRANCH}'.

Start from either:

  ${BASE_BRANCH}

or resume the publishing branch:

  ${UPDATE_BRANCH}

Then run:

  ./publish.sh"
fi

STARTING_DEV_COMMIT="$(git rev-parse "${BASE_BRANCH}")"

printf "\n📋 Local changes found:\n\n"

if [[ -n "$(git status --porcelain)" ]]; then
  git status --short
else
  printf "   No local changes yet. Generated files may still need refreshing.\n"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 3. Create or resume the publishing branch
# ─────────────────────────────────────────────────────────────────────────────

info "Moving this update onto the working branch..."

if git show-ref --verify --quiet "refs/heads/${UPDATE_BRANCH}"; then
  git switch "$UPDATE_BRANCH"
  success "Resuming the existing local publishing branch."
elif git ls-remote --exit-code --heads \
  "$REMOTE" "$UPDATE_BRANCH" >/dev/null 2>&1; then
  git switch --track -c "$UPDATE_BRANCH" "${REMOTE}/${UPDATE_BRANCH}"
  success "Resuming the existing publishing branch from GitHub."
else
  git switch -c "$UPDATE_BRANCH"
  success "Created a new publishing branch."
fi

success "Your changes are now safely on:"
printf "🌿 %s\n" "$UPDATE_BRANCH"
printf "\n📍 Publishing details\n"
printf "────────────────────────────────────\n"
printf "🌿 Working branch: %s\n" "$UPDATE_BRANCH"
printf "🌱 Base branch:    %s\n" "$BASE_BRANCH"
printf "📦 Repository:     %s\n" "$REPO"

info "Checking GitHub for newer changes on ${BASE_BRANCH}..."

git fetch "$REMOTE" "$BASE_BRANCH"

REMOTE_DEV_COMMIT="$(git rev-parse "${REMOTE}/${BASE_BRANCH}")"

if [[ "$STARTING_DEV_COMMIT" == "$REMOTE_DEV_COMMIT" ]]; then
  success "The working branch is already based on the latest ${BASE_BRANCH}."
elif git merge-base --is-ancestor \
  "$STARTING_DEV_COMMIT" \
  "$REMOTE_DEV_COMMIT"; then

  info "A newer version of ${BASE_BRANCH} exists. Updating the working branch..."

  if ! git rebase --autostash "${REMOTE}/${BASE_BRANCH}"; then
    warning "Git could not apply the update automatically.

Your work is still safe on:
  ${UPDATE_BRANCH}

Resolve the reported conflicts, then continue with:

  git add -A
  git rebase --continue
  ./publish.sh

Or cancel the rebase with:

  git rebase --abort"

    exit 1
  fi

  success "The working branch now includes the latest ${BASE_BRANCH} changes."
elif git merge-base --is-ancestor \
  "$REMOTE_DEV_COMMIT" \
  "$STARTING_DEV_COMMIT"; then

  fail "Your local ${BASE_BRANCH} contains commits that are not on GitHub.

Your changes are safe on:
  ${UPDATE_BRANCH}

Review the local commits before publishing:

  git log ${REMOTE}/${BASE_BRANCH}..${UPDATE_BRANCH} --oneline"
else
  fail "Your local ${BASE_BRANCH} has diverged from GitHub.

Your changes are safe on:
  ${UPDATE_BRANCH}

A manual Git review is required before publishing."
fi

# ─────────────────────────────────────────────────────────────────────────────
# 4. Validate feed.rss
# ─────────────────────────────────────────────────────────────────────────────

info "Checking feed.rss..."

[[ -f "$ROOT/feed.rss" ]] ||
  fail "feed.rss is missing from the repository root."

python3 <<'PY'
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

path = Path("feed.rss")
data = path.read_bytes()

def stop(message: str) -> None:
    print(f"\n❌ {message}", file=sys.stderr)
    print(
        """
How to copy the raw Substack feed:

1. Open:
   https://burnoutseries.substack.com/feed.rss

2. Right-click the feed view.

3. Choose “View Page Source” or “Show Page Source”.

4. Copy the complete raw XML source.

5. Replace the contents of feed.rss with that source.

6. Make sure <?xml or <rss is the first content in the file.

7. Run ./publish.sh again.
""",
        file=sys.stderr,
    )
    raise SystemExit(1)

if not data:
    stop("feed.rss is empty.")

if data.startswith(b"\xef\xbb\xbf"):
    stop("feed.rss begins with a UTF-8 byte-order mark.")

if data[:1] in {b" ", b"\t", b"\r", b"\n"}:
    stop("feed.rss contains whitespace before the XML document.")

preview = data[:500].lower()

if b"<!doctype html" in preview or b"<html" in preview:
    stop("feed.rss contains a rendered HTML page instead of raw RSS XML.")

if not data.startswith((b"<?xml", b"<rss")):
    stop("feed.rss does not begin with an XML declaration or RSS element.")

try:
    root = ET.fromstring(data)
except ET.ParseError as error:
    stop(f"feed.rss is not valid XML: {error}")

root_name = root.tag.rsplit("}", 1)[-1].lower()

if root_name != "rss":
    stop(f"The root element is <{root_name}>, not <rss>.")

channel = root.find("channel")

if channel is None:
    stop("The RSS document does not contain a channel element.")

items = channel.findall("item")

if not items:
    stop("The RSS feed does not contain any post items.")

print(f"✅ feed.rss is valid and contains {len(items)} post item(s).")
PY

success "feed.rss passed validation."

# ─────────────────────────────────────────────────────────────────────────────
# 5. Prepare an isolated Python environment
# ─────────────────────────────────────────────────────────────────────────────

info "Preparing the local publishing tools..."

TEMP_DIR="$(mktemp -d)"
VENV_PATH="${TEMP_DIR}/venv"

if ! python3 -m venv "$VENV_PATH" >/dev/null 2>&1; then
  fail "Python could not create a temporary virtual environment.

On Ubuntu or Debian, install the venv package:

  sudo apt-get install python3-venv

Then run ./publish.sh again."
fi

# shellcheck disable=SC1091
source "${VENV_PATH}/bin/activate"

python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r scripts/requirements.txt

success "Python dependencies are ready."

# ─────────────────────────────────────────────────────────────────────────────
# 6. Generate the knowledge files
# ─────────────────────────────────────────────────────────────────────────────

info "Generating posts.md and posts.json..."

python main.py

success "Post knowledge files were generated."

info "Generating imgs.json..."

GITHUB_OWNER="${REPO%/*}"
GITHUB_REPO="${REPO#*/}"

success "Image index was generated."

# ─────────────────────────────────────────────────────────────────────────────
# 7. Review generated changes
# ─────────────────────────────────────────────────────────────────────────────

info "Reviewing the generated knowledge base..."

python -m json.tool posts.json >/dev/null
python -m json.tool imgs.json >/dev/null

if [[ -f manifest.json ]]; then
  python -m json.tool manifest.json >/dev/null
fi

success "All generated files are valid."

CHANGED_FILES="$(git status --porcelain)"

if [[ -z "$CHANGED_FILES" ]]; then
  warning "No changes were detected."

  git switch "$BASE_BRANCH"
  git reset --hard "${REMOTE}/${BASE_BRANCH}"
  git branch -D "$UPDATE_BRANCH"
  git fetch "$REMOTE" --prune

  success "Everything is already up to date. The temporary branch has been removed."
  exit 0
fi

POSTS_CHANGED="No"
IMGS_CHANGED="No"
RSS_CHANGED="No"

git diff --quiet -- posts.md || POSTS_CHANGED="Yes"
git diff --quiet -- imgs.json || IMGS_CHANGED="Yes"
git diff --quiet -- feed.rss || RSS_CHANGED="Yes"

IMAGE_COUNT="$(git status --porcelain imgs/ | wc -l | tr -d ' ')"

printf "\n📊 Publishing summary\n"
printf "────────────────────────────────────\n"
printf "📡 RSS updated:              %s\n" "$RSS_CHANGED"
printf "📝 Posts regenerated:        %s\n" "$POSTS_CHANGED"
printf "🖼️  Image index regenerated: %s\n" "$IMGS_CHANGED"
printf "📷 Image files changed:      %s\n" "$IMAGE_COUNT"

printf "\n📋 Files to be published:\n\n"
git status --short

success "The knowledge base is ready to publish."

# ─────────────────────────────────────────────────────────────────────────────
# 8. Commit and push
# ─────────────────────────────────────────────────────────────────────────────

if ! confirm "Commit and push these changes to GitHub?"; then
  warning "Publishing stopped before the commit.

Your changes remain on branch:
  ${UPDATE_BRANCH}"
  exit 0
fi

info "Creating the commit..."

git add -A

if git diff --cached --quiet; then
  success "No new changes needed committing."
else
  git commit -m "$COMMIT_MESSAGE"
  success "Changes committed."
fi

info "Pushing ${UPDATE_BRANCH} to GitHub..."

if git rev-parse \
  --abbrev-ref \
  --symbolic-full-name \
  '@{upstream}' >/dev/null 2>&1; then

  git push
else
  git push --set-upstream "$REMOTE" "$UPDATE_BRANCH"
fi

success "Branch pushed to GitHub."

# ─────────────────────────────────────────────────────────────────────────────
# 9. Open a pull request
# ─────────────────────────────────────────────────────────────────────────────

info "Checking for an existing pull request into ${BASE_BRANCH}..."

PR_URL="$(
  gh pr list \
    --repo "$REPO" \
    --head "$UPDATE_BRANCH" \
    --base "$BASE_BRANCH" \
    --state open \
    --json url \
    --jq '.[0].url // empty'
)"

if [[ -n "$PR_URL" ]]; then
  success "Resuming the existing pull request:"
  printf "🔗 %s\n" "$PR_URL"
else
  info "Opening a pull request into ${BASE_BRANCH}..."

  PR_URL="$(
    gh pr create \
      --repo "$REPO" \
      --base "$BASE_BRANCH" \
      --head "$UPDATE_BRANCH" \
      --title "Update Burnout Series knowledge base" \
      --body "## Knowledge-base update

This pull request was created by \`publish.sh\`.

It refreshes the repository inputs and generated knowledge files, including:

- \`feed.rss\`
- \`posts.md\`
- \`posts.json\`
- \`imgs.json\`
- relevant imagery or supporting files
"
  )"

  success "Pull request opened:"
  printf "🔗 %s\n" "$PR_URL"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 10. Merge into dev
# ─────────────────────────────────────────────────────────────────────────────

if ! confirm "Merge this pull request into ${BASE_BRANCH} now?"; then
  warning "The pull request remains open for review:"
  printf "🔗 %s\n" "$PR_URL"
  exit 0
fi

info "Merging the pull request..."

if ! gh pr merge "$PR_URL" \
  --repo "$REPO" \
  --squash \
  --delete-branch; then

  fail "GitHub could not merge the pull request automatically.

This may be caused by required reviews, checks or branch-protection rules.

Open the pull request and complete the merge manually:
${PR_URL}"
fi

success "The update was merged into ${BASE_BRANCH}."

# ─────────────────────────────────────────────────────────────────────────────
# 11. Tidy up
# ─────────────────────────────────────────────────────────────────────────────

info "Tidying up the local repository..."

git switch "$BASE_BRANCH"
git fetch "$REMOTE" "$BASE_BRANCH"
git reset --hard "${REMOTE}/${BASE_BRANCH}"
git fetch "$REMOTE" --prune

if git show-ref --verify --quiet "refs/heads/${UPDATE_BRANCH}"; then
  git branch -D "$UPDATE_BRANCH"
fi

success "Publishing complete. Everything is synchronized and tidy. 🎉"

printf "\n📚 Updated knowledge files:\n"
printf "   • posts.md\n"
printf "   • posts.json\n"
printf "   • imgs.json\n\n"
