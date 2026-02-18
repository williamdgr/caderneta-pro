from datetime import datetime
from pathlib import Path
import shutil

from database.connection import get_db_path


def create_startup_backup(max_files=7):
    db_path = get_db_path()
    if not db_path.exists():
        return None

    backup_dir = db_path.parent / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"caderneta_backup_{timestamp}.db"
    backup_path = backup_dir / backup_name

    shutil.copy2(db_path, backup_path)
    _cleanup_old_backups(backup_dir, max_files=max_files)

    return backup_path


def _cleanup_old_backups(backup_dir: Path, max_files=7):
    backup_files = sorted(
        backup_dir.glob("caderneta_backup_*.db"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )

    for old_file in backup_files[max_files:]:
        old_file.unlink(missing_ok=True)


def get_latest_backups(limit=7):
    db_path = get_db_path()
    backup_dir = db_path.parent / "backup"
    if not backup_dir.exists():
        return []

    backup_files = sorted(
        backup_dir.glob("caderneta_backup_*.db"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )[:limit]

    backups = []
    for backup_file in backup_files:
        stats = backup_file.stat()
        backups.append(
            {
                "name": backup_file.name,
                "datetime": datetime.fromtimestamp(stats.st_mtime),
                "size_bytes": stats.st_size,
            }
        )

    return backups


def restore_backup(backup_file_path):
    backup_path = Path(backup_file_path)
    if not backup_path.exists():
        raise FileNotFoundError("Arquivo de backup não encontrado.")

    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, db_path)
    return db_path
