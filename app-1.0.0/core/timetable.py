"""课程表"""

import json
import os
import re

from core.constants import DATA_PROFILE, ensure_data_dirs

ensure_data_dirs()

PROFILES_DIR = DATA_PROFILE


class TimetableProfile:

    def __init__(self, name="档案配置-1"):
        self.name = name
        self.default_class_duration = 40
        self.default_break_duration = 10
        self.periods = []
        self.courses = {}

    def to_dict(self):
        return {
            "name": self.name,
            "defaultClassDuration": self.default_class_duration,
            "defaultBreakDuration": self.default_break_duration,
            "periods": self.periods,
            "courses": self.courses,
        }

    @classmethod
    def from_dict(cls, d):
        p = cls(d.get("name", "档案配置-1"))
        p.default_class_duration = d.get("defaultClassDuration", 40)
        p.default_break_duration = d.get("defaultBreakDuration", 10)
        p.periods = d.get("periods", [])
        p.courses = d.get("courses", {})
        return p

    def save(self, filepath=None):
        if filepath is None:
            filepath = get_profile_path(self.name)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def add_period(self, period_type, start, end):
        self.periods.append({"type": period_type, "start": start, "end": end})
        idx = len(self.periods) - 1
        self.courses[str(idx)] = {}

    def remove_period(self, index):
        if 0 <= index < len(self.periods):
            self.periods.pop(index)
            new_courses = {}
            for i in range(len(self.periods)):
                key = str(i)
                old_key = str(i) if i < index else str(i + 1)
                new_courses[key] = self.courses.pop(old_key, {})
            self.courses = new_courses

    def get_next_start_time(self):
        if not self.periods:
            return "08:00"
        return self.periods[-1]["end"]

    def period_count(self):
        return len(self.periods)


def get_profile_path(name):
    return os.path.join(PROFILES_DIR, f"{name}.json")


def list_profiles():
    os.makedirs(PROFILES_DIR, exist_ok=True)
    pattern = re.compile(r"^档案配置-\d+\.json$")
    files = [f for f in os.listdir(PROFILES_DIR) if pattern.match(f)]
    files.sort(key=lambda x: int(re.search(r"\d+", x).group()))
    return [os.path.splitext(f)[0] for f in files]


def next_profile_name():
    names = list_profiles()
    if not names:
        return "档案配置-1"
    nums = [int(re.search(r"\d+", n).group()) for n in names]
    return f"档案配置-{max(nums) + 1}"


def ensure_default_profile():
    names = list_profiles()
    if not names:
        name = "档案配置-1"
        profile = TimetableProfile(name)
        profile.save()
        return name
    return names[-1]


def rename_profile(old_name, new_name):
    old_path = get_profile_path(old_name)
    new_path = get_profile_path(new_name)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)


def delete_profile(name):
    path = get_profile_path(name)
    if os.path.exists(path):
        os.remove(path)
