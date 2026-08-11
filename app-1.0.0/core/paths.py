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

"""
路径初始化模块
"""

import json
import os
import sys
from pathlib import Path


def _detect_package_root() -> str:
    env_root = os.environ.get("Glimpseon_PackageRoot")
    if env_root and os.path.isdir(env_root):
        return os.path.normpath(env_root)

    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))

    current = Path(__file__).resolve()
    return str(current.parent.parent.parent)


def _detect_app_dir(package_root: str) -> str:
    env_app = os.environ.get("Glimpseon_AppDir")
    if env_app and os.path.isdir(env_app):
        return os.path.normpath(env_app)

    try:
        for entry in os.listdir(package_root):
            if not entry.startswith("app-"):
                continue
            record_path = os.path.join(package_root, entry, "record.json")
            if not os.path.isfile(record_path):
                continue
            try:
                with open(record_path, 'r', encoding='utf-8') as f:
                    record = json.load(f)
                if record.get("current", 0) == 1 and not record.get("partial", False):
                    return os.path.join(package_root, entry)
            except (json.JSONDecodeError, OSError):
                continue
    except OSError:
        pass

    return package_root


def _detect_meipass() -> str | None:
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', None)
    return None


PACKAGE_ROOT = _detect_package_root()
APP_DIR = _detect_app_dir(PACKAGE_ROOT)
MEIPASS_DIR = _detect_meipass()

DATA_ROOT = os.path.join(PACKAGE_ROOT, "data")
DATA_CONFIG = os.path.join(DATA_ROOT, "config")
DATA_LOG = os.path.join(DATA_ROOT, "log")
DATA_CACHE = os.path.join(DATA_ROOT, "cache")
DATA_TEMP = os.path.join(DATA_ROOT, "temp")
DATA_PROFILE = os.path.join(DATA_ROOT, "profile")
DATA_USER = os.path.join(DATA_ROOT, "user")
DATA_ICON = os.path.join(DATA_ROOT, "icon")
DATA_WALLPAPER = os.path.join(DATA_ROOT, "wallpaper")
DATA_CLASSPHOTOS = os.path.join(DATA_ROOT, "classphotos")
DATA_NOTES = os.path.join(DATA_ROOT, "notes")

BASE_DIR = PACKAGE_ROOT
WALLPAPER_DIR = DATA_WALLPAPER

_record_path = os.path.join(APP_DIR, "record.json")
try:
    with open(_record_path, 'r', encoding='utf-8') as _f:
        _record = json.load(_f)
    VERSION = _record.get("version", "1.0.0")
    BUILD_DATE = _record.get("build_date", "")
except (json.JSONDecodeError, OSError):
    VERSION = "1.0.0"
    BUILD_DATE = ""


def ensure_data_dirs():
    dirs = [
        DATA_ROOT, DATA_CONFIG, DATA_LOG, DATA_CACHE,
        DATA_TEMP, DATA_PROFILE, DATA_USER, DATA_ICON, DATA_WALLPAPER,
        DATA_CLASSPHOTOS, DATA_NOTES
    ]
    for d in dirs:
        if not os.path.exists(d):
            try:
                os.makedirs(d, exist_ok=True)
            except OSError:
                pass


def get_resource_path(relative_path: str) -> str:
    """查找顺序：APP_DIR MEIPASS_DIR  APP_DIR"""
    app_path = os.path.join(APP_DIR, relative_path)
    if os.path.exists(app_path):
        return app_path

    if MEIPASS_DIR:
        meipass_path = os.path.join(MEIPASS_DIR, relative_path)
        if os.path.exists(meipass_path):
            return meipass_path

    return app_path