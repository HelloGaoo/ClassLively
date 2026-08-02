# Glimpseon
# Copyright (C) 2026 HelloGaoo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""record.json 管理"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("Glimpseon.core.record")


def scan_files(directory: Path) -> dict:
    files = {}
    directory = Path(directory)

    for file in directory.rglob("*"):
        if file.is_file() and file.name != "record.json":
            try:
                rel_path = file.relative_to(directory)
                files[str(rel_path)] = {
                    "hash": hashlib.sha256(file.read_bytes()).hexdigest(),
                    "size": file.stat().st_size
                }
            except Exception as e:
                logger.warning(f"扫描文件失败 {file}: {e}")

    return files


def create_record(version: str, app_dir: Path, current: int = 1, partial: bool = False) -> dict:
    return {
        "current": current,
        "partial": partial,
        "version": version,
        "files": scan_files(app_dir),
        "variables": {
            "install_time": datetime.now().isoformat()
        }
    }


def save_record(record: dict, record_path: Path):
    try:
        record_path = Path(record_path)
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"record.json 已保存: {record_path}")
        return True
    except Exception as e:
        logger.error(f"保存 record.json 失败: {e}")
        return False


def load_record(record_path: Path) -> dict:
    try:
        record_path = Path(record_path)
        if not record_path.exists():
            return None
        return json.loads(record_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"加载 record.json 失败: {e}")
        return None


def deactivate_version(version_dir: Path):
    version_dir = Path(version_dir)
    record_path = version_dir / "record.json"

    record = load_record(record_path)
    if record:
        record["current"] = 0
        save_record(record, record_path)
        logger.info(f"版本已取消激活: {version_dir}")
