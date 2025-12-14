import os
import pytest
import tempfile
import pathlib
from backend.src.utils.security import BoxedPath, atomic_writer, SecurityError

@pytest.fixture
def sandbox_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield pathlib.Path(tmpdir).resolve()

def test_boxed_path_valid(sandbox_root):
    # Test simple valid path
    path = sandbox_root / "test.txt"
    boxed = BoxedPath("test.txt", sandbox_root)
    assert boxed.full_path == path

def test_boxed_path_nested_valid(sandbox_root):
    # Test nested valid path
    path = sandbox_root / "subdir" / "test.txt"
    boxed = BoxedPath("subdir/test.txt", sandbox_root)
    assert boxed.full_path == path

def test_boxed_path_traversal_attempt(sandbox_root):
    # Test simple traversal
    with pytest.raises(SecurityError):
        BoxedPath("../outside.txt", sandbox_root)

def test_boxed_path_absolute_traversal(sandbox_root):
    # Test absolute path outside root should be re-rooted
    # e.g. /etc/passwd -> {root}/etc/passwd
    boxed = BoxedPath("/etc/passwd", sandbox_root)
    expected = sandbox_root / "etc" / "passwd"
    assert boxed.full_path == expected

def test_boxed_path_symlink_attack(sandbox_root):
    # Create a symlink inside root pointing outside
    # Note: This requires OS support for symlinks
    target = sandbox_root.parent / "target_outside.txt"
    target.touch()
    
    link = sandbox_root / "link_to_outside"
    try:
        os.symlink(target, link)
        
        # This should fail because the resolved path is outside
        with pytest.raises(SecurityError):
            BoxedPath("link_to_outside", sandbox_root)
            
    finally:
        if target.exists():
            target.unlink()

def test_atomic_writer(sandbox_root):
    target = sandbox_root / "atomic.txt"
    boxed = BoxedPath("atomic.txt", sandbox_root)
    
    with atomic_writer(boxed, "w") as f:
        f.write("content")
        # File shouldn't exist at target yet (or at least not with new content if it was large)
        # But atomic_writer writes to temp file first.
        
    assert target.exists()
    assert target.read_text() == "content"

def test_atomic_writer_failure(sandbox_root):
    target = sandbox_root / "fail.txt"
    boxed = BoxedPath("fail.txt", sandbox_root)
    
    try:
        with atomic_writer(boxed, "w") as f:
            f.write("partial")
            raise RuntimeError("Simulated failure")
    except RuntimeError:
        pass
        
    # Target should NOT exist
    assert not target.exists()
