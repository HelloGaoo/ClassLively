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
Glimpseon 启动器
"""
# 本模块参考：ClassIsland（https://github.com/ClassIsland/ClassIsland）
import json
import os
import subprocess
import sys
from pathlib import Path


def find_and_launch():
    root = Path(__file__).parent.resolve()
    app_dirs = [d for d in root.iterdir() 
                if d.is_dir() and d.name.startswith("app-")]
    if not app_dirs:
        sys.exit("找不到app目录")
    
    valid_versions = []
    for app_dir in app_dirs:
        record_path = app_dir / "record.json"
        if not record_path.exists():
            print(f"跳过 {app_dir.name}: 无 record.json")
            continue
        
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"跳过 {app_dir.name}: record.json 解析失败 - {e}")
            continue
        
        if record.get("partial", False):
            print(f"跳过 {app_dir.name}")
            continue
        
        version_str = app_dir.name.replace("app-", "")
        try:
            version_parts = version_str.split(".")
            version = tuple(map(int, version_parts))
        except:
            version = (0, 0, 0)
        
        valid_versions.append({
            "path": app_dir,
            "version": version,
            "current": record.get("current", 0)
        })
    
    if not valid_versions:
        print("找不到app")
        return 1
    
    valid_versions.sort(key=lambda x: (
        -x["current"],
        -x["version"][0] if len(x["version"]) > 0 else 0,
        -x["version"][1] if len(x["version"]) > 1 else 0,
        -x["version"][2] if len(x["version"]) > 2 else 0
    ))

    selected = valid_versions[0]["path"]
    main_py = selected / "GlimpseonMain.py"
    
    if not main_py.exists():
        print(f"找不到主程序 {main_py}")
        return 1
    
    print(f"启动版本: {selected.name}")
    
    env = os.environ.copy()
    env["Glimpseon_PackageRoot"] = str(root)
    env["Glimpseon_AppDir"] = str(selected)
    
    return subprocess.run([sys.executable, str(main_py)], env=env).returncode


if __name__ == "__main__":
    sys.exit(find_and_launch())