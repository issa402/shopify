#!/usr/bin/env bash
# This script blocks accidental commits or pushes of large files.
set -euo pipefail

# GitHub rejects files over 100 MB, so this project blocks at 50 MB for safety.
readonly LIMIT_BYTES="${LARGE_FILE_LIMIT_BYTES:-52428800}"

# Convert a byte count into MiB for readable error messages.
bytes_to_mib() {
  # awk keeps this portable without needing Python or Node on the host.
  awk -v bytes="$1" 'BEGIN { printf "%.1f MiB", bytes / 1024 / 1024 }'
}

# Print a consistent failure message for every oversized file.
report_large_file() {
  # The first argument is the path that would be committed or pushed.
  local path="$1"
  # The second argument is the file size in bytes.
  local size="$2"
  # Human-readable output helps you know exactly what to remove or move to LFS.
  printf 'Blocked large file: %s (%s)\n' "$path" "$(bytes_to_mib "$size")" >&2
}

# Check files currently staged for commit.
check_staged_files() {
  # Track whether any staged file exceeds the safety limit.
  local failed=0

  # Read staged added/copied/modified/renamed paths without breaking on spaces.
  while IFS= read -r path; do
    # Deleted files and submodule entries do not have regular file sizes here.
    [[ -f "$path" ]] || continue

    # stat returns the staged path's current working-tree size in bytes.
    local size
    size="$(stat -c '%s' "$path")"

    # Any file over the limit is blocked before it enters history.
    if (( size > LIMIT_BYTES )); then
      report_large_file "$path" "$size"
      failed=1
    fi
  done < <(git diff --cached --name-only --diff-filter=ACMR)

  # A non-zero exit tells Git to stop the commit.
  return "$failed"
}

# Check blobs in a commit range before push.
check_object_range() {
  local range="$1"
  local failed=0

  while IFS=' ' read -r object path; do
    local type
    type="$(git cat-file -t "$object" 2>/dev/null || true)"
    [[ "$type" == "blob" ]] || continue

    local size
    size="$(git cat-file -s "$object")"
    if (( size > LIMIT_BYTES )); then
      report_large_file "${path:-$object}" "$size"
      failed=1
    fi
  done < <(git rev-list --objects "$range")

  return "$failed"
}

# Read pre-push refs from stdin and check exactly what Git is about to upload.
check_pre_push_ranges() {
  local failed=0

  while read -r local_ref local_sha remote_ref remote_sha; do
    [[ "$local_sha" != "0000000000000000000000000000000000000000" ]] || continue

    local range
    if [[ "$remote_sha" == "0000000000000000000000000000000000000000" ]]; then
      range="$local_sha"
    else
      range="${remote_sha}..${local_sha}"
    fi

    check_object_range "$range" || failed=1
  done

  return "$failed"
}

# Dispatch based on the hook mode.
case "${1:-}" in
  # pre-commit passes --staged to scan the index.
  --staged)
    check_staged_files
    ;;
  # pre-push passes --pre-push and provides refs on stdin.
  --pre-push)
    check_pre_push_ranges
    ;;
  # Unknown usage should fail loudly so hooks are not silently misconfigured.
  *)
    echo "Usage: $0 --staged | --pre-push" >&2
    exit 2
    ;;
esac
