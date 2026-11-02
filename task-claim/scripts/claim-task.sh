#!/usr/bin/env bash
# Claims a task so two chats, agents or worktrees on this machine don't pick up the same one.
#
#   claim-task.sh claim <scope> <id> [--owner NAME] [--branch BRANCH]
#                                          take the task (exit 1 if someone else holds it)
#   claim-task.sh release <scope> <id> [--owner NAME] [--force]
#                                          free it (only its holder, unless --force)
#   claim-task.sh check <scope> <id> [--owner NAME]
#                                          exit 0 when free or yours, 1 when held by someone else
#   claim-task.sh list                     every claim in this repo, with holder, branch and age
#   claim-task.sh --self-test              prove the lock works, in a temporary directory
#
# <scope> groups ids (a Task Master tag, a milestone, "gh" for issue numbers). Claims live in the
# repository's shared git directory (claims/<scope>-<id>), so every worktree of this clone sees them,
# whatever branch it is on. They never reach the remote. `mkdir` makes a claim atomic.
# Holder = --owner (else $CLAIM_OWNER, else $USER) plus the branch. Two chats on one branch need
# different --owner names, or they look like the same holder.
# A claim older than 24 hours is marked STALE but never taken over silently: ask its holder,
# then release it with --force.
set -uo pipefail

stale_after=$((24 * 60 * 60))

claims_dir() {
    if [[ -n "${CLAIMS_DIR:-}" ]]; then
        printf '%s\n' "$CLAIMS_DIR"
    else
        local common
        common="$(git rev-parse --path-format=absolute --git-common-dir)" || return 1
        printf '%s/claims\n' "$common"
    fi
}

usage() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }

field() { sed -n "s/^$1=//p" "$2/info" 2>/dev/null | head -1; }
human() {
    local s="$1"
    if ((s >= 3600)); then echo "$((s / 3600))h"; elif ((s >= 60)); then echo "$((s / 60))m"; else echo "${s}s"; fi
}
describe() {
    local dir="$1" age
    age=$(($(date +%s) - $(field since "$dir")))
    printf '%s (branch %s, %s ago%s)' "$(field owner "$dir")" "$(field branch "$dir")" "$(human "$age")" \
        "$([[ $age -gt $stale_after ]] && echo ', STALE')"
}
current_branch() { git branch --show-current 2>/dev/null; }
default_owner() { printf '%s' "${CLAIM_OWNER:-${USER:-unknown}}"; }

# True when the claim in $1 belongs to owner $2 (empty = default) on branch $3 (empty = current).
is_mine() {
    local dir="$1" owner="${2:-$(default_owner)}" branch="${3:-$(current_branch)}"
    [[ "$(field owner "$dir")" == "$owner" && "$(field branch "$dir")" == "$branch" ]]
}

cmd_claim() {
    local scope="$1" id="$2" owner="$3" branch="$4" root dir
    root="$(claims_dir)" || exit 2
    mkdir -p "$root"
    dir="$root/$scope-$id"
    [[ -n "$branch" ]] || branch="$(current_branch)"
    [[ -n "$owner" ]] || owner="$(default_owner)"
    if mkdir "$dir" 2>/dev/null; then
        printf 'owner=%s\nbranch=%s\nsince=%s\npath=%s\n' "$owner" "$branch" "$(date +%s)" "$PWD" > "$dir/info"
        echo "Claimed $scope/$id for $owner."
        return 0
    fi
    if is_mine "$dir" "$owner" "$branch"; then echo "Already yours: $scope/$id."; return 0; fi
    echo "Task $scope/$id is held by $(describe "$dir")." >&2
    echo "Pick another task, or ask its holder to release it." >&2
    return 1
}

cmd_release() {
    local scope="$1" id="$2" owner="$3" force="$4" root dir
    root="$(claims_dir)" || exit 2
    dir="$root/$scope-$id"
    if [[ ! -d "$dir" ]]; then echo "Task $scope/$id has no claim."; return 0; fi
    if [[ -z "$force" ]] && ! is_mine "$dir" "$owner" ""; then
        echo "Task $scope/$id is held by $(describe "$dir"); release it as that holder, or pass --force." >&2
        return 1
    fi
    rm -rf "$dir"
    echo "Released $scope/$id."
}

cmd_check() {
    local scope="$1" id="$2" owner="$3" root dir
    root="$(claims_dir)" || exit 2
    dir="$root/$scope-$id"
    if [[ ! -d "$dir" ]]; then echo "Task $scope/$id is free."; return 0; fi
    if is_mine "$dir" "$owner" ""; then echo "Task $scope/$id is yours."; return 0; fi
    echo "Task $scope/$id is held by $(describe "$dir")." >&2
    return 1
}

cmd_list() {
    local root dir found=0
    root="$(claims_dir)" || exit 2
    for dir in "$root"/*/; do
        [[ -f "${dir}info" ]] || continue
        found=1
        printf '%-24s %s\n' "$(basename "$dir")" "$(describe "${dir%/}")"
    done
    ((found)) || echo "No claims."
}

self_test() {
    local tmp me listing fails=0
    tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' RETURN
    export CLAIMS_DIR="$tmp/claims"
    me="$0"
    expect() { # expect <exit> <description> <command...>
        local want="$1" what="$2"; shift 2
        "$@" >/dev/null 2>&1; local got=$?
        if [[ $got -ne $want ]]; then echo "FAIL: $what (exit $got, wanted $want)"; fails=$((fails + 1)); else echo "ok:   $what"; fi
    }
    expect 0 "a free task can be claimed" "$me" claim t 1 --owner alice
    expect 1 "a held task is refused to another owner" "$me" claim t 1 --owner bob
    expect 0 "the holder may claim again" "$me" claim t 1 --owner alice
    expect 0 "a different task is independent" "$me" claim t 2 --owner bob
    expect 0 "check passes for the holder" "$me" check t 1 --owner alice
    expect 1 "check fails for another owner on the same branch" "$me" check t 1 --owner bob
    expect 1 "release is refused to another owner" "$me" release t 1 --owner bob
    expect 2 "a stray argument is a usage error" "$me" claim t 3 --bogus
    expect 0 "release by the holder works" "$me" release t 1 --owner alice
    expect 0 "a released task can be claimed again" "$me" claim t 1 --owner bob
    expect 0 "release --force frees any claim" "$me" release t 1 --force
    expect 0 "claim for the stale check" "$me" claim t 1 --owner bob
    sed -i.bak "s/^since=.*/since=1/" "$CLAIMS_DIR/t-1/info" && rm -f "$CLAIMS_DIR/t-1/info.bak"
    listing="$("$me" list)"
    if [[ "$listing" == *STALE* ]]; then echo "ok:   an old claim is marked stale"; else echo "FAIL: stale claim not marked"; fails=$((fails + 1)); fi
    ( "$me" claim race 1 --owner a >/dev/null 2>&1 & "$me" claim race 1 --owner b >/dev/null 2>&1 & wait )
    if [[ "$(grep -c '^owner=' "$CLAIMS_DIR/race-1/info")" == 1 ]]; then echo "ok:   a race leaves one holder"; else echo "FAIL: race"; fails=$((fails + 1)); fi
    ((fails == 0)) && echo "Self-test passed." || { echo "$fails check(s) failed."; return 1; }
}

parse_opts() { # parse_opts <args...>; sets owner, branch, force
    owner=""; branch=""; force=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --owner) [[ $# -ge 2 ]] || usage; owner="$2"; shift 2 ;;
            --branch) [[ $# -ge 2 ]] || usage; branch="$2"; shift 2 ;;
            --force) force=1; shift ;;
            *) usage ;;
        esac
    done
}

case "${1:-}" in
    claim)   [[ $# -ge 3 ]] || usage; parse_opts "${@:4}"; cmd_claim "$2" "$3" "$owner" "$branch" ;;
    release) [[ $# -ge 3 ]] || usage; parse_opts "${@:4}"; cmd_release "$2" "$3" "$owner" "$force" ;;
    check)   [[ $# -ge 3 ]] || usage; parse_opts "${@:4}"; cmd_check "$2" "$3" "$owner" ;;
    list)    cmd_list ;;
    --self-test) self_test ;;
    *) usage ;;
esac
