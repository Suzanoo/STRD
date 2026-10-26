"""Local macOS/POSIX storage: compare under advisory lock, backup, atomic replace."""
from contextlib import contextmanager
import os
from pathlib import Path
import stat
import tempfile
from .format import MAX_BYTES, ProjectError, decode, digest, encode

class ConflictError(ProjectError):
    pass

class SaveError(ProjectError):
    pass


def location(path):
    p=Path(path).expanduser().absolute()
    if p.name.endswith(('.bak','.lock')) or '.pending-' in p.name:
        raise ProjectError('Use a project filename, not a recovery or lock sidecar.')
    # Resolve directory aliases so cooperating instances share one lock. Reject file
    # symlinks/hardlinks: atomic replacement would otherwise break alias semantics.
    return p.parent.resolve(strict=True)/p.name


def read_bytes(path):
    flags=os.O_RDONLY | getattr(os,'O_NOFOLLOW',0) | getattr(os,'O_NONBLOCK',0)
    fd=os.open(path,flags)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise ProjectError('Only regular, non-hardlinked local project files are supported.')
        if info.st_size>MAX_BYTES:raise ProjectError('Project exceeds 16 MiB limit.')
        with os.fdopen(fd,'rb',closefd=False) as stream:raw=stream.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:raise ProjectError('Project exceeds 16 MiB limit.')
        return raw
    finally:os.close(fd)


@contextmanager
def locked(path):
    try:import fcntl
    except ImportError:raise SaveError('Safe project writes require the macOS/POSIX pilot runtime.') from None
    lock=Path(str(path)+'.lock')
    fd=os.open(lock,os.O_RDWR|os.O_CREAT|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0),0o600)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise SaveError('Unsafe project lock file.')
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ConflictError('Another instance is saving. Retry after it finishes.') from None
        yield
    finally:os.close(fd)  # OS releases lock on normal exit or process death. Never unlink it.


def sync_directory(directory):
    fd=os.open(directory,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def stage(path,raw):
    fd,name=tempfile.mkstemp(prefix=path.name+'.pending-',dir=path.parent)
    p=Path(name)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        # Independent readback before replacement.
        if read_bytes(p)!=raw:raise SaveError('Staged file verification failed.')
        decode(raw)
        return p
    except BaseException:
        p.unlink(missing_ok=True);raise


def load(path):
    p=location(path);raw=read_bytes(p)
    return decode(raw),digest(raw),p


def recover(path):
    """Read previous successful revision; never modify damaged original."""
    candidate=Path(path)
    original=str(candidate)[:-4] if candidate.name.endswith('.bak') else candidate
    p=location(original);return decode(read_bytes(Path(str(p)+'.bak')))


def save(path,doc,expected):
    """expected=None means create only, including Save As. Never silently overwrite."""
    staged=None;backup_stage=None;replaced=False
    try:
        p=location(path);raw=encode(doc)
        with locked(p):
            try:old=read_bytes(p)
            except FileNotFoundError:old=None
            actual=digest(old) if old is not None else None
            if actual!=expected:raise ConflictError('Project changed, disappeared, or destination exists. Open the latest file or Save As a new filename.')
            if old is not None:decode(old)  # Never rotate corruption over a good backup.
            if old == raw:return digest(raw),p  # Do not erase previous revision on unchanged Save.
            staged=stage(p,raw)
            if old is not None:
                backup=Path(str(p)+'.bak')
                # Reject unsafe sidecar targets; never follow or overwrite links.
                if backup.is_symlink():raise SaveError('Backup path is a symlink.')
                if backup.exists():read_bytes(backup)
                backup_stage=stage(backup,old)
                os.replace(backup_stage,backup);backup_stage=None
                sync_directory(p.parent)
            # Recheck external, non-cooperating edits immediately before commit.
            try:latest=read_bytes(p)
            except FileNotFoundError:latest=None
            if (digest(latest) if latest is not None else None)!=expected:raise ConflictError('Project changed during save. Save As a new filename.')
            if expected is None:
                # link is create-only: even a racing external creator cannot be overwritten.
                os.link(staged,p);replaced=True;staged.unlink();staged=None
            else:
                os.replace(staged,p);staged=None;replaced=True
            sync_directory(p.parent)
        return digest(raw),p
    except ProjectError:raise
    except OSError as exc:
        suffix=' File may have been committed; reopen to verify, or Save As a new name. Workspace remains unsaved.' if replaced else ' Original project remains unchanged; workspace remains unsaved.'
        raise SaveError(str(exc)+suffix) from exc
    finally:
        for p in (staged,backup_stage):
            if p is not None:
                try:p.unlink(missing_ok=True)
                except OSError:pass
