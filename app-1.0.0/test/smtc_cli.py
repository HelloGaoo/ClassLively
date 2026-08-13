"""
SMTC CLI
控制键:
    空格           播放 / 暂停
    ←  / →        上一首 / 下一首
    S             保存缩略图
    R             立即刷新一次
    ESC           退出
"""

import asyncio
import ctypes
import os
import sys
import threading
import time
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)
from winsdk.windows.storage.streams import Buffer, InputStreamOptions


# Closed=0 Opened=1 Changing=2 Stopped=3 Playing=4 Paused=5
STATUS_MAP = {
    PlaybackStatus.CLOSED: "closed",
    PlaybackStatus.OPENED: "opened",
    PlaybackStatus.CHANGING: "changing",
    PlaybackStatus.STOPPED: "stopped",
    PlaybackStatus.PLAYING: "playing",
    PlaybackStatus.PAUSED: "paused",
}

AUTO_REPEAT_MAP = {0: "none", 1: "track", 2: "list"}
PLAYBACK_TYPE_MAP = {0: "unknown", 1: "music", 2: "video", 3: "image", 4: "file"}


class C:
    """ANSI 颜色"""
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def fmt_time(seconds: float) -> str:
    if seconds is None:
        return "--:--"
    if seconds < 0:
        seconds = 0
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def fmt_td(td) -> str:
    if td is None:
        return "None"
    try:
        return fmt_time(td.total_seconds())
    except Exception:
        return "?"


def safe_getattr(obj, name, default="<n/a>"):
    try:
        v = getattr(obj, name, default)
        return v
    except Exception as e:
        return f"<err:{e}>"


class SmtcCli:
    def __init__(self):
        self._manager = None
        self._loop = None
        self._stop = False
        self._status_msg = ""
        self._status_color = C.GRAY
        self._save_dir = os.path.dirname(os.path.abspath(__file__))

    async def _init_manager(self):
        if self._manager is None:
            self._manager = await MediaManager.request_async()

    async def _read_session(self, session):
        data = {}
        try:
            data["app_user_model_id"] = session.source_app_user_model_id
        except Exception as e:
            data["app_user_model_id"] = f"<err: {e}>"

        try:
            data["playback"] = session.get_playback_info()
        except Exception as e:
            data["playback"] = None
            data["playback_err"] = str(e)

        try:
            data["timeline"] = session.get_timeline_properties()
        except Exception as e:
            data["timeline"] = None
            data["timeline_err"] = str(e)

        try:
            data["props"] = await session.try_get_media_properties_async()
        except Exception as e:
            data["props"] = None
            data["props_err"] = str(e)

        return data

    async def gather(self):
        await self._init_manager()
        current = self._manager.get_current_session()
        sessions = self._manager.get_sessions()
        n = sessions.size
        result = []
        current_aumid = ""
        try:
            current_aumid = current.source_app_user_model_id if current else ""
        except Exception:
            pass

        for i in range(n):
            s = sessions.get_at(i)
            try:
                aumid = s.source_app_user_model_id
            except Exception:
                aumid = ""
            is_cur = (aumid != "" and aumid == current_aumid)
            data = await self._read_session(s)
            result.append((i, is_cur, data, s))
        return result

    def _render(self, sessions_data):
        sys.stdout.write("\033[2J\033[H")
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{C.CYAN}{C.BOLD}SMTC读取 [{now}] {C.RESET}")
        print(f"{C.GRAY}空格 播放/暂停   ← 上一首   → 下一首   S 保存缩略图   R 刷新   ESC 退出{C.RESET}")
        print(f"会话总数: {len(sessions_data)}")
        if self._status_msg:
            print(f"{self._status_color}[{self._status_msg}]{C.RESET}")
        else:
            print()
        if not sessions_data:
            print(f"{C.YELLOW}无活跃媒体会话{C.RESET}")
            return

        for idx, is_cur, data, session in sessions_data:
            mark = f"{C.GREEN}*{C.RESET}" if is_cur else " "
            print(f"\n{mark} [{C.CYAN}{idx}{C.RESET}] ", end="")
            self._print_session(data)

    def _print_session(self, data):
        app = data.get("app_user_model_id", "")
        print(f"{C.BOLD}{app}{C.RESET}")

        pb = data.get("playback")
        if pb is None:
            print(f"  播放信息: {C.RED}不可用 ({data.get('playback_err', '?')}){C.RESET}")
        else:
            status_val = safe_getattr(pb, "playback_status", None)
            status_name = STATUS_MAP.get(status_val, str(status_val))
            color = C.GREEN if status_name == "playing" else (
                C.YELLOW if status_name == "paused" else C.GRAY)
            print(f"  播放状态   : {color}{status_name}{C.RESET} (value={getattr(status_val, 'value', '?')})")

            ctrls = safe_getattr(pb, "controls", None)
            if ctrls is not None:
                fields = [
                    ("play", "is_play_enabled"),
                    ("pause", "is_pause_enabled"),
                    ("stop", "is_stop_enabled"),
                    ("next", "is_next_enabled"),
                    ("prev", "is_previous_enabled"),
                    ("seek", "is_seek_enabled"),
                    ("shuffle", "is_shuffle_enabled"),
                    ("repeat", "is_repeat_enabled"),
                    ("ffwd", "is_fast_forward_enabled"),
                    ("rewind", "is_rewind_enabled"),
                    ("chan_up", "is_channel_up_enabled"),
                    ("chan_down", "is_channel_down_enabled"),
                ]
                parts = []
                for label, attr in fields:
                    v = safe_getattr(ctrls, attr, None)
                    if v is None:
                        continue
                    parts.append(f"{label}={'Y' if v else 'N'}")
                print(f"  控件可用性 : {', '.join(parts)}")

            arm = safe_getattr(pb, "auto_repeat_mode", None)
            if arm is not None and arm != "<n/a>":
                arm_v = getattr(arm, "value", arm)
                print(f"  循环模式   : {AUTO_REPEAT_MAP.get(arm_v, arm_v)} (value={arm_v})")

            shuf = safe_getattr(pb, "is_shuffle_active", None)
            if shuf is not None and shuf != "<n/a>":
                print(f"  随机激活   : {shuf}")

            rate = safe_getattr(pb, "playback_rate", None)
            if rate is not None and rate != "<n/a>":
                print(f"  播放速率   : {rate}")

            rtype = safe_getattr(pb, "playback_rate_type", None)
            if rtype is not None and rtype != "<n/a>":
                print(f"  速率类型   : {getattr(rtype, 'value', rtype)}")

        tl = data.get("timeline")
        if tl is None:
            print(f"  时间线     : {C.RED}不可用 ({data.get('timeline_err', '?')}){C.RESET}")
        else:
            print(
                f"  时间线     : pos={fmt_td(safe_getattr(tl, 'position', None))} / "
                f"end={fmt_td(safe_getattr(tl, 'end_time', None))}  "
                f"start={fmt_td(safe_getattr(tl, 'start_time', None))}  "
                f"min={fmt_td(safe_getattr(tl, 'min_seek_time', None))}  "
                f"max={fmt_td(safe_getattr(tl, 'max_seek_time', None))}"
            )

        props = data.get("props")
        if props is None:
            print(f"  媒体属性   : {C.RED}不可用 ({data.get('props_err', '?')}){C.RESET}")
            return

        title = safe_getattr(props, "title", "") or ""
        artist = safe_getattr(props, "artist", "") or ""
        album = safe_getattr(props, "album_title", "") or ""
        album_artist = safe_getattr(props, "album_artist", "") or ""
        subtitle = safe_getattr(props, "subtitle", "") or ""
        track = safe_getattr(props, "track_number", 0)
        genres_raw = safe_getattr(props, "genres", None)
        ptype = safe_getattr(props, "playback_type", None)

        print(f"  标题       : {C.BOLD}{title}{C.RESET}")
        print(f"  艺术家     : {artist}")
        print(f"  专辑       : {album}")
        if album_artist and album_artist != artist:
            print(f"  专辑艺术家 : {album_artist}")
        if subtitle:
            print(f"  副标题     : {subtitle}")
        if track:
            print(f"  音轨号     : {track}")
        try:
            genres_list = list(genres_raw) if genres_raw else []
        except Exception:
            genres_list = []
        if genres_list:
            print(f"  流派       : {genres_list}")
        if ptype is not None and ptype != "<n/a>":
            ptype_v = getattr(ptype, "value", ptype)
            print(f"  媒体类型   : {PLAYBACK_TYPE_MAP.get(ptype_v, ptype_v)} (value={ptype_v})")

        thumb = None
        if hasattr(props, "thumbnail"):
            try:
                thumb = props.thumbnail
            except Exception:
                thumb = None
        print(f"  缩略图     : {'{0} 存在 (按 S 保存)'.format(C.GREEN) if thumb else '无'}{C.RESET}")

    async def _refresh_loop(self):
        while not self._stop:
            try:
                sessions_data = await self.gather()
                self._render(sessions_data)
            except Exception as e:
                print(f"{C.RED}读取异常: {e}{C.RESET}")
            try:
                await asyncio.wait_for(asyncio.shield(self._wait_stop()), timeout=1.0)
            except asyncio.TimeoutError:
                pass

    async def _wait_stop(self):
        while not self._stop:
            await asyncio.sleep(0.1)

    async def _exec_command(self, cmd):
        await self._init_manager()
        session = self._manager.get_current_session()
        if not session:
            self._set_status("无当前会话", C.YELLOW)
            return
        try:
            if cmd == "play_pause":
                pb = session.get_playback_info()
                playing = pb and pb.playback_status == PlaybackStatus.PLAYING
                if playing:
                    ok = await session.try_pause_async()
                    self._set_status(f"暂停 -> {'OK' if ok else 'FAIL'}",
                                     C.GREEN if ok else C.RED)
                else:
                    ok = await session.try_play_async()
                    self._set_status(f"播放 -> {'OK' if ok else 'FAIL'}",
                                     C.GREEN if ok else C.RED)
            elif cmd == "next":
                ok = await session.try_skip_next_async()
                self._set_status(f"下一首 -> {'OK' if ok else 'FAIL'}",
                                 C.GREEN if ok else C.RED)
            elif cmd == "prev":
                ok = await session.try_skip_previous_async()
                self._set_status(f"上一首 -> {'OK' if ok else 'FAIL'}",
                                 C.GREEN if ok else C.RED)
            elif cmd == "save_thumb":
                await self._save_thumbnail(session)
        except Exception as e:
            self._set_status(f"命令失败: {e}", C.RED)

    async def _save_thumbnail(self, session):
        props = await session.try_get_media_properties_async()
        if not props:
            self._set_status("媒体属性不可用", C.YELLOW)
            return
        if not getattr(props, "thumbnail", None):
            self._set_status("无缩略图", C.YELLOW)
            return
        stream = await props.thumbnail.open_read_async()
        if not stream or stream.size <= 0:
            self._set_status("缩略图流为空", C.YELLOW)
            return
        buf = Buffer(stream.size)
        await stream.read_async(buf, buf.capacity, InputStreamOptions.READ_AHEAD)
        b = bytes(buf)
        if b.startswith(b"\xff\xd8\xff"):
            ext = "jpg"
        elif b.startswith(b"\x89PNG"):
            ext = "png"
        else:
            ext = "bin"
        title = (getattr(props, "title", "") or "thumb").strip()
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in title)[:40]
        if not safe:
            safe = "thumb"
        path = os.path.join(self._save_dir, f"smtc_{safe}.{ext}")
        with open(path, "wb") as f:
            f.write(b)
        self._set_status(f"缩略图已保存: {path} ({len(b)} bytes)", C.GREEN)

    def _set_status(self, msg, color):
        self._status_msg = msg
        self._status_color = color

    def _keyboard_loop(self):
        import msvcrt
        while not self._stop:
            if not msvcrt.kbhit():
                time.sleep(0.02)
                continue
            ch = msvcrt.getch()
            if ch in (b"\x00", b"\xe0"):
                ch2 = msvcrt.getch()
                if ch2 == b"K":
                    self._schedule("prev")
                elif ch2 == b"M":
                    self._schedule("next")
            elif ch == b" ":
                self._schedule("play_pause")
            elif ch in (b"s", b"S"):
                self._schedule("save_thumb")
            elif ch in (b"r", b"R"):
                pass
            elif ch == b"\x1b":
                self._stop = True
                break

    def _schedule(self, cmd):
        if self._loop and not self._loop.is_closed():
            try:
                asyncio.run_coroutine_threadsafe(self._exec_command(cmd), self._loop)
            except RuntimeError:
                pass

    async def run(self):
        self._loop = asyncio.get_running_loop()
        kb = threading.Thread(target=self._keyboard_loop, daemon=True)
        kb.start()
        try:
            await self._refresh_loop()
        finally:
            self._stop = True


def enable_vt():
    try:
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        k.GetConsoleMode(h, ctypes.byref(mode))
        k.SetConsoleMode(h, mode.value | 0x0007)
    except Exception:
        pass


def main():
    enable_vt()
    cli = SmtcCli()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
