"""Bounded ingestion of untrusted data. Never check out or execute project code."""
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import time
import unicodedata
from urllib.parse import urlsplit
import zipfile
import zlib

from backend.services.workspaces import RepositoryError, WorkspaceRegistry

MAX_UPLOAD = 25 * 1024 * 1024
MAX_ENTRIES = 10000
MAX_FILE = 10 * 1024 * 1024
MAX_EXTRACTED = 100 * 1024 * 1024
MAX_STAGE = 256 * 1024 * 1024
MAX_DEPTH = 30
ZIP_SECONDS = 30
GIT_SECONDS = 60
CHUNK = 64 * 1024
VCS_NAMES = {".git", ".hg", ".svn"}
RESERVED = re.compile(r"^(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\.|$)", re.I)


def github_url(value: str) -> str:
    """Accept only an ASCII HTTPS github.com repository root, never credentials."""
    if not value.isascii() or any(ord(c) <= 32 or ord(c) == 127 for c in value):
        raise RepositoryError(422, "Expected a public github.com HTTPS repository URL")
    try:
        parsed = urlsplit(value)
        valid = (parsed.scheme == "https" and parsed.netloc.lower() == "github.com"
                 and not parsed.query and not parsed.fragment and "?" not in value
                 and "#" not in value)
        match = re.fullmatch(r"/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9_.-]{1,100})/?", parsed.path)
        if not valid or not match:
            raise ValueError
        owner, repo = match.groups()
        if repo.endswith(".git"):
            repo = repo[:-4]
        if not repo or repo in {".", ".."} or owner.endswith("-"):
            raise ValueError
    except ValueError:
        raise RepositoryError(422, "Expected a public github.com HTTPS repository URL") from None
    return "https://github.com/{}/{}".format(owner, repo)


def member_parts(name: str):
    """Portable, conservative filenames, shared by ZIP and Git materialization."""
    if (not name or name.startswith("/") or "\\" in name or ":" in name
            or any(ord(c) < 32 or ord(c) == 127 for c in name)):
        raise RepositoryError(422, "Unsafe repository member path")
    parts = (name[:-1] if name.endswith("/") else name).split("/")
    if len(parts) > MAX_DEPTH or len(name.encode("utf-8")) > 4096:
        raise RepositoryError(422, "Repository path exceeds limits")
    for part in parts:
        if (part in {"", ".", ".."} or part.endswith((".", " "))
                or RESERVED.match(part) or part.casefold() in VCS_NAMES
                or len(part.encode("utf-8")) > 255):
            raise RepositoryError(422, "Unsafe repository member path")
    return parts


class MemberIndex:
    """Reject duplicate entries and implicit parent/file or case collisions."""
    def __init__(self):
        self.paths = {}
        self.explicit = set()

    def add(self, name, directory=False):
        parts = member_parts(name)
        for index in range(1, len(parts) + 1):
            path = "/".join(parts[:index])
            key = unicodedata.normalize("NFC", path).casefold()
            kind = "directory" if index < len(parts) or directory else "file"
            previous = self.paths.get(key)
            if previous is not None and previous != (path, kind):
                raise RepositoryError(422, "Colliding repository members")
            if index == len(parts):
                if key in self.explicit:
                    raise RepositoryError(422, "Duplicate repository member")
                self.explicit.add(key)
            self.paths[key] = (path, kind)
        return parts


def _destination(root, parts):
    target = root.joinpath(*parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise RepositoryError(422, "Unsafe repository member path")
    return target


def extract_zip(archive: Path, destination: Path) -> Path:
    deadline = time.monotonic() + ZIP_SECONDS
    if archive.stat().st_size > MAX_UPLOAD:
        raise RepositoryError(413, "ZIP upload exceeds limit")
    destination.mkdir(mode=0o700)
    try:
        with zipfile.ZipFile(archive) as bundle:
            members = bundle.infolist()
            if not members or len(members) > MAX_ENTRIES:
                raise RepositoryError(413 if members else 422, "ZIP entry count is invalid")
            index = MemberIndex()
            planned = []
            declared = 0
            for entry in members:
                if time.monotonic() > deadline:
                    raise RepositoryError(504, "ZIP extraction timed out")
                # orig_filename preserves NULs that ZipInfo.filename truncates.
                parts = index.add(entry.orig_filename, entry.is_dir())
                mode = stat.S_IFMT(entry.external_attr >> 16)
                if mode not in {0, stat.S_IFDIR, stat.S_IFREG}:
                    raise RepositoryError(422, "ZIP links and special files are forbidden")
                if (mode == stat.S_IFDIR and not entry.is_dir()) or (mode == stat.S_IFREG and entry.is_dir()):
                    raise RepositoryError(422, "Inconsistent ZIP member type")
                if entry.flag_bits & 1 or entry.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                    raise RepositoryError(422, "Encrypted or unsupported ZIP archive")
                declared += entry.file_size
                if entry.file_size > MAX_FILE or declared > MAX_EXTRACTED:
                    raise RepositoryError(413, "Extracted repository exceeds limits")
                if entry.is_dir() and entry.file_size:
                    raise RepositoryError(422, "Invalid ZIP directory")
                planned.append((entry, parts))
            total = 0
            for entry, parts in planned:
                if time.monotonic() > deadline:
                    raise RepositoryError(504, "ZIP extraction timed out")
                target = _destination(destination, parts)
                if entry.is_dir():
                    target.mkdir(mode=0o700, parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                count = 0
                with bundle.open(entry) as source, target.open("xb") as output:
                    os.chmod(target, 0o600)
                    while True:
                        if time.monotonic() > deadline:
                            raise RepositoryError(504, "ZIP extraction timed out")
                        data = source.read(CHUNK)
                        if not data:
                            break
                        count += len(data)
                        total += len(data)
                        if count > MAX_FILE or total > MAX_EXTRACTED:
                            raise RepositoryError(413, "Extracted repository exceeds limits")
                        output.write(data)
                if count != entry.file_size:
                    raise RepositoryError(422, "Invalid ZIP member size")
    except (zipfile.BadZipFile, zlib.error, NotImplementedError, RuntimeError, EOFError, UnicodeError, OSError):
        raise RepositoryError(422, "Invalid or unreadable ZIP archive") from None
    children = list(destination.iterdir())
    return children[0] if len(children) == 1 and children[0].is_dir() else destination


def import_zip(registry: WorkspaceRegistry, stream, filename: str):
    with registry.staging() as stage:
        archive = stage / "upload.zip"
        total = 0
        with archive.open("xb") as output:
            while True:
                data = stream.read(CHUNK)
                if not data:
                    break
                total += len(data)
                if total > MAX_UPLOAD:
                    raise RepositoryError(413, "ZIP upload exceeds limit")
                output.write(data)
        root = extract_zip(archive, stage / "project")
        archive.unlink()
        name = re.sub(r"[^A-Za-z0-9_. -]", "_", filename.replace("\\", "/").split("/")[-1])[:100]
        name = name[:-4] if name.lower().endswith(".zip") else name
        return registry.publish(stage, root, "zip", name or "Uploaded project")


def _stage_bytes(stage):
    total = 0
    for current, dirs, files in os.walk(stage, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
        for name in files:
            try:
                total += (Path(current) / name).lstat().st_size
            except FileNotFoundError:
                pass
    return total


def _git_environment(stage):
    home = stage / "environment"
    home.mkdir(mode=0o700)
    return {
        "PATH": os.defpath, "HOME": str(home), "XDG_CONFIG_HOME": str(home),
        "LANG": "C", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0",
        "GIT_ALLOW_PROTOCOL": "https", "GIT_ATTR_NOSYSTEM": "1",
        "GIT_LFS_SKIP_SMUDGE": "1",
    }


def _run_git(executable, args, stage, env, deadline, limit, input_bytes=b""):
    """Bounded output and process-group timeout. Only called with fixed Git commands.

    Disk polling is a soft staging ceiling; deployment must enforce a hard quota.
    stdout/stderr spool in quota-monitored staging; only bounded results are read.
    """
    command = [executable,
               "-c", "credential.helper=", "-c", "credential.interactive=false",
               "-c", "http.followRedirects=false", "-c", "http.sslVerify=true",
               "-c", "core.hooksPath=" + os.devnull,
               "-c", "init.templateDir=", "-c", "protocol.allow=never",
               "-c", "protocol.https.allow=always", *args]
    with tempfile.TemporaryFile(dir=str(stage)) as stdin, \
            tempfile.NamedTemporaryFile(dir=str(stage)) as stdout, \
            tempfile.NamedTemporaryFile(dir=str(stage)) as stderr:
        stdin.write(input_bytes)
        stdin.seek(0)
        try:
            process = subprocess.Popen(command, cwd=str(stage), env=env,
                                       stdin=stdin, stdout=stdout, stderr=stderr,
                                       shell=False, start_new_session=True)
        except OSError:
            raise RepositoryError(503, "Git executable unavailable") from None
        try:
            while True:
                if time.monotonic() >= deadline:
                    raise RepositoryError(504, "GitHub import timed out")
                if (os.fstat(stdout.fileno()).st_size > limit
                        or os.fstat(stderr.fileno()).st_size > 1024 * 1024
                        or _stage_bytes(stage) > MAX_STAGE):
                    raise RepositoryError(413, "GitHub repository exceeds import limits")
                if process.poll() is not None:
                    break
                time.sleep(0.05)
            if process.returncode != 0:
                raise RepositoryError(404, "Public GitHub repository unavailable")
            stdout.seek(0)
            result = stdout.read(limit + 1)
            if len(result) > limit:
                raise RepositoryError(413, "GitHub repository exceeds import limits")
            return result
        finally:
            # Also terminate any surviving transport children after parent exit.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()


def import_github(registry: WorkspaceRegistry, url: str):
    canonical = github_url(url)
    executable = shutil.which("git", path=os.defpath)
    if not executable:
        raise RepositoryError(503, "Git executable unavailable")
    with registry.staging() as stage:
        deadline = time.monotonic() + GIT_SECONDS
        env = _git_environment(stage)
        clone = stage / "objects"
        _run_git(executable, ["clone", "--depth=1", "--single-branch", "--no-tags",
                             "--no-checkout", "--", canonical + ".git", str(clone)],
                 stage, env, deadline, 1024 * 1024)
        git_dir = "--git-dir=" + str(clone / ".git")
        commit = _run_git(executable, [git_dir, "rev-parse", "--verify", "HEAD"],
                          stage, env, deadline, 128).decode("ascii").strip()
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
            raise RepositoryError(422, "Invalid Git commit")
        listing = _run_git(executable, [git_dir, "ls-tree", "-r", "-l", "-z", commit],
                           stage, env, deadline, 4 * 1024 * 1024)
        records = listing.rstrip(b"\0").split(b"\0") if listing else []
        if len(records) > MAX_ENTRIES:
            raise RepositoryError(413, "GitHub repository exceeds entry limit")
        index = MemberIndex()
        files = []
        total = 0
        warnings = set()
        try:
            for record in records:
                metadata, raw_name = record.split(b"\t", 1)
                mode, kind, oid, size = metadata.split()
                parts = index.add(raw_name.decode("utf-8"))
                if mode in {b"120000", b"160000"}:
                    warnings.add("Symbolic links and submodules were omitted")
                    continue
                if mode not in {b"100644", b"100755"} or kind != b"blob" or not re.fullmatch(b"[0-9a-f]{40}|[0-9a-f]{64}", oid):
                    raise ValueError
                count = int(size)
                total += count
                if count < 0 or count > MAX_FILE or total > MAX_EXTRACTED:
                    raise RepositoryError(413, "GitHub repository exceeds extracted limits")
                files.append((oid, count, parts))
        except (ValueError, UnicodeError):
            raise RepositoryError(422, "Unsupported Git repository tree") from None
        # cat-file reads raw objects: no checkout, smudge filters, attributes or hooks.
        payload = _run_git(executable, [git_dir, "cat-file", "--batch"], stage, env,
                           deadline, MAX_EXTRACTED + MAX_ENTRIES * 128,
                           b"".join(oid + b"\n" for oid, _, _ in files)) if files else b""
        project = stage / "project"
        project.mkdir(mode=0o700)
        position = 0
        for oid, size, parts in files:
            if time.monotonic() >= deadline:
                raise RepositoryError(504, "GitHub import timed out")
            end = payload.find(b"\n", position)
            expected = oid + b" blob " + str(size).encode("ascii")
            if end < 0 or payload[position:end] != expected:
                raise RepositoryError(422, "Invalid Git object stream")
            position = end + 1
            if payload[position + size:position + size + 1] != b"\n":
                raise RepositoryError(422, "Invalid Git object stream")
            target = _destination(project, parts)
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open("xb") as output:
                os.chmod(target, 0o600)
                output.write(memoryview(payload)[position:position + size])
            position += size + 1
        if position != len(payload):
            raise RepositoryError(422, "Invalid Git object stream")
        if any((project.joinpath(*parts)).read_bytes().startswith(b"version https://git-lfs.github.com/spec/v1\n")
               for _, size, parts in files if size < 1024):
            warnings.add("Git LFS pointers were retained; LFS objects were not downloaded")
        shutil.rmtree(clone)
        shutil.rmtree(stage / "environment")
        return registry.publish(stage, project, "github", canonical.rsplit("/", 1)[-1],
                                {"github_url": canonical, "commit_sha": commit}, sorted(warnings))
