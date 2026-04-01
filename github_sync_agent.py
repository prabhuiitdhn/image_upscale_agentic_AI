import json
import os
import re
import subprocess
import urllib.error
import urllib.request


GITHUB_FILE_SIZE_LIMIT_BYTES = 100 * 1024 * 1024


def _run_git(args, check=True):
    """Run a git command and return completed process."""
    return subprocess.run(
        ["git"] + args,
        check=check,
        text=True,
        capture_output=True,
    )


def _tracked_files_exceeding_limit(limit_bytes=GITHUB_FILE_SIZE_LIMIT_BYTES):
    """Return tracked files that exceed GitHub's regular file size limit."""
    tracked = _run_git(["ls-files"], check=True)
    oversized = []
    for rel_path in tracked.stdout.splitlines():
        if not rel_path:
            continue
        if os.path.isfile(rel_path):
            size = os.path.getsize(rel_path)
            if size > limit_bytes:
                oversized.append((rel_path, size))
    return oversized


def _format_size_mb(size_bytes):
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def _extract_owner_repo(repo_link):
    """Extract owner/repo from common GitHub HTTPS or SSH links."""
    pattern = r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$"
    match = re.search(pattern, repo_link.strip())
    if not match:
        raise ValueError("Invalid GitHub repository link format.")
    owner, repo = match.group(1), match.group(2)
    return owner, repo


def _github_api_request(url, method="GET", token=None, payload=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "image-resolution-github-agent",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8")
        parsed = {}
        try:
            parsed = json.loads(error_body) if error_body else {}
        except json.JSONDecodeError:
            parsed = {"message": error_body}
        return exc.code, parsed


def _create_repo_if_missing(repo_link, private_repo=True):
    owner, repo = _extract_owner_repo(repo_link)
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "Remote repo does not exist and GITHUB_TOKEN is not set. "
            "Set GITHUB_TOKEN to allow automatic repository creation."
        )

    status, me = _github_api_request("https://api.github.com/user", token=token)
    if status != 200:
        raise RuntimeError(f"Unable to validate GITHUB_TOKEN: {me}")

    authenticated_user = me.get("login")
    payload = {"name": repo, "private": private_repo}

    if owner.lower() == str(authenticated_user).lower():
        create_url = "https://api.github.com/user/repos"
    else:
        create_url = f"https://api.github.com/orgs/{owner}/repos"

    create_status, create_response = _github_api_request(
        create_url,
        method="POST",
        token=token,
        payload=payload,
    )

    if create_status in (201, 202):
        print(f"Repository created: {owner}/{repo}")
        return

    if create_status == 422:
        msg = str(create_response.get("message", ""))
        if "already exists" in msg.lower():
            print(f"Repository already exists: {owner}/{repo}")
            return

    raise RuntimeError(f"Failed to create repository: {create_response}")


def _ensure_git_initialized():
    if not os.path.exists(".git"):
        _run_git(["init"])
        print("Initialized new git repository.")


def _ensure_origin(repo_link, branch):
    remote_result = _run_git(["remote"], check=False)
    remotes = set(remote_result.stdout.split())

    if "origin" in remotes:
        _run_git(["remote", "set-url", "origin", repo_link])
    else:
        _run_git(["remote", "add", "origin", repo_link])

    remote_check = _run_git(["ls-remote", "origin"], check=False)
    if remote_check.returncode != 0:
        print("Remote repository not reachable. Trying to create it on GitHub...")
        _create_repo_if_missing(repo_link)


def _ensure_branch_name():
    branch_result = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], check=False)
    current_branch = branch_result.stdout.strip()
    if not current_branch or current_branch == "HEAD":
        current_branch = "main"
        _run_git(["checkout", "-b", current_branch], check=False)
    return current_branch


def run_github_sync_agent(default_repo_link="", default_visibility="private"):
    repo_link = input(
        f"Enter GitHub repository link [{default_repo_link}]: "
    ).strip() or default_repo_link
    if not repo_link:
        raise ValueError("Repository link is required.")

    visibility = input(
        f"Visibility (private/public) [{default_visibility}]: "
    ).strip().lower() or default_visibility
    private_repo = visibility != "public"

    commit_message = input("Enter commit message: ").strip()
    if not commit_message:
        raise ValueError("Commit message is required.")

    _ensure_git_initialized()
    branch = _ensure_branch_name()

    _run_git(["add", "-A"])
    status = _run_git(["status", "--porcelain"], check=False)
    if status.stdout.strip():
        _run_git(["commit", "-m", commit_message])
        print("Created commit.")
    else:
        print("No changes to commit.")

    oversized = _tracked_files_exceeding_limit()
    if oversized:
        print("Push blocked: tracked files exceed GitHub 100 MB file limit.")
        for path, size in oversized:
            print(f"- {path}: {_format_size_mb(size)}")
        print("Resolve by using Git LFS or removing these files from git tracking.")
        raise RuntimeError("Push aborted due to oversized tracked files.")

    _ensure_origin(repo_link, branch)
    try:
        _run_git(["push", "-u", "origin", branch], check=True)
        print("Repository sync completed.")
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout.strip())
        if exc.stderr:
            print(exc.stderr.strip())
        raise RuntimeError("Push failed. See error details above.") from exc


if __name__ == "__main__":
    run_github_sync_agent()
