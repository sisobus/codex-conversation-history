#!/usr/bin/env python3
"""
Codex Conversation History Viewer
A simple CLI tool to browse Codex conversation history
"""

import json
import os
import sys
import termios
import tty
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    """ANSI color codes for terminal output."""

    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


CODEX_DIR = Path.home() / ".codex" / "sessions"
VERSION = "1.0.1"


class InteractiveMenu:
    """Simple interactive menu using arrow keys."""

    def __init__(self) -> None:
        self.selected_index = 0

    def get_key(self) -> str:
        """Read a single keypress from stdin."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)

            # Handle escape sequences (arrow keys, etc.)
            if key == "\x1b":
                key += sys.stdin.read(2)

            return key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        os.system("clear")

    def display_menu(
        self,
        items: List[str],
        title: str = "",
        paginate: bool = False,
        items_per_page: int = 10,
    ) -> int:
        """Display an interactive menu and return the selected index."""
        self.selected_index = 0
        current_page = 0
        total_items = len(items)

        if paginate and total_items > items_per_page:
            total_pages = (total_items + items_per_page - 1) // items_per_page
        else:
            paginate = False
            total_pages = 1
            items_per_page = total_items if total_items > 0 else 1

        while True:
            self.clear_screen()

            if title:
                print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.END}")
                print("=" * len(title))
                print()

            if paginate:
                print(
                    f"{Colors.GRAY}Use ↑/↓ to navigate, PgUp/PgDn for pages, Enter to select, 'q' to quit{Colors.END}"
                )
                print(
                    f"{Colors.YELLOW}Page {current_page + 1}/{total_pages} (Total: {total_items} items){Colors.END}"
                )
            else:
                print(
                    f"{Colors.GRAY}Use ↑/↓ to navigate, Enter to select, 'q' to quit{Colors.END}"
                )
            print()

            start_idx = current_page * items_per_page
            end_idx = min(start_idx + items_per_page, total_items)
            visible_items = items[start_idx:end_idx]

            for i, item in enumerate(visible_items):
                actual_index = start_idx + i
                if actual_index == self.selected_index:
                    print(f"{Colors.GREEN}▶ {item}{Colors.END}")
                else:
                    print(f"  {item}")

            key = self.get_key()

            if key == "\x1b[A":  # Up arrow
                if self.selected_index > start_idx:
                    self.selected_index -= 1
                elif paginate and current_page > 0:
                    current_page -= 1
                    new_start = current_page * items_per_page
                    new_end = min(new_start + items_per_page, total_items)
                    self.selected_index = max(new_start, new_end - 1)
            elif key == "\x1b[B":  # Down arrow
                if self.selected_index < min(end_idx - 1, total_items - 1):
                    self.selected_index += 1
                elif paginate and current_page < total_pages - 1:
                    current_page += 1
                    self.selected_index = current_page * items_per_page
            elif key == "\x1b[5~" and paginate:  # Page Up
                if current_page > 0:
                    current_page -= 1
                    self.selected_index = current_page * items_per_page
            elif key == "\x1b[6~" and paginate:  # Page Down
                if current_page < total_pages - 1:
                    current_page += 1
                    self.selected_index = current_page * items_per_page
            elif key in ("\r", "\n"):
                return self.selected_index
            elif key in ("q", "\x03"):  # q or Ctrl+C
                self.clear_screen()
                print("Goodbye!")
                sys.exit(0)


class CodexHistoryViewer:
    """Main class for viewing Codex conversation history."""

    def __init__(self) -> None:
        self.menu = InteractiveMenu()
        self.sessions_dir = CODEX_DIR

        if not self.sessions_dir.exists():
            print(
                f"{Colors.RED}Error: Codex sessions directory not found at {self.sessions_dir}{Colors.END}"
            )
            sys.exit(1)

    @staticmethod
    def _parse_iso_timestamp(timestamp: Optional[str]) -> Optional[datetime]:
        if not timestamp:
            return None
        try:
            if timestamp.endswith("Z"):
                timestamp = timestamp[:-1] + "+00:00"
            return datetime.fromisoformat(timestamp)
        except Exception:
            return None

    def get_dates(self) -> List[Tuple[str, Path]]:
        """Collect available dates (year/month/day) with session files."""
        date_entries: List[Tuple[str, Path, datetime]] = []

        for year_dir in self.sessions_dir.iterdir():
            if not year_dir.is_dir():
                continue
            try:
                year = int(year_dir.name)
            except ValueError:
                continue

            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                try:
                    month = int(month_dir.name)
                except ValueError:
                    continue

                for day_dir in month_dir.iterdir():
                    if not day_dir.is_dir():
                        continue
                    try:
                        day = int(day_dir.name)
                    except ValueError:
                        continue

                    session_files = [
                        file_path
                        for file_path in day_dir.glob("*.jsonl")
                        if file_path.is_file() and not file_path.name.startswith(".")
                    ]
                    if not session_files:
                        continue

                    date_value = datetime(year=year, month=month, day=day)
                    count = len(session_files)
                    label = (
                        f"{date_value.strftime('%Y-%m-%d')} "
                        f"({count} {'session' if count == 1 else 'sessions'})"
                    )
                    date_entries.append((label, day_dir, date_value))

        date_entries.sort(key=lambda item: item[2], reverse=True)
        return [(label, path) for label, path, _ in date_entries]

    def get_sessions(self, day_path: Path) -> List[Tuple[str, Path]]:
        """List session files for a given day."""
        session_entries: List[Tuple[str, Path, datetime]] = []

        for jsonl_file in day_path.glob("*.jsonl"):
            if not jsonl_file.is_file() or jsonl_file.name.startswith("."):
                continue

            metadata = self._read_session_metadata(jsonl_file)
            started_at = metadata.get("timestamp")
            started_dt = (
                self._parse_iso_timestamp(started_at)
                if isinstance(started_at, str)
                else None
            )
            if not started_dt:
                started_dt = datetime.fromtimestamp(jsonl_file.stat().st_mtime)

            cwd = metadata.get("cwd")
            cwd_label = f" - {Path(cwd).name}" if cwd else ""
            display_name = f"{started_dt.strftime('%H:%M')} - {jsonl_file.name}{cwd_label}"
            session_entries.append((display_name, jsonl_file, started_dt))

        session_entries.sort(key=lambda item: item[2], reverse=True)
        return [(label, path) for label, path, _ in session_entries]

    @staticmethod
    def _read_session_metadata(jsonl_path: Path) -> Dict[str, Optional[str]]:
        """Read the first line to extract metadata such as timestamp and cwd."""
        try:
            with open(jsonl_path, "r", encoding="utf-8") as file:
                first_line = file.readline()
                if not first_line.strip():
                    return {}
                data = json.loads(first_line)
                if data.get("type") != "session_meta":
                    return {}
                payload = data.get("payload", {})
                return {
                    "timestamp": payload.get("timestamp") or data.get("timestamp"),
                    "cwd": payload.get("cwd"),
                    "originator": payload.get("originator"),
                }
        except Exception:
            return {}

    @staticmethod
    def _extract_text(content: object) -> str:
        """Extract textual content from Codex payload entries."""
        parts: List[str] = []

        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type")
                    if item_type in {"input_text", "output_text", "text"}:
                        text = item.get("text")
                        if text:
                            parts.append(text)
                elif isinstance(item, str):
                    parts.append(item)

        return "\n".join(part for part in parts if part).strip()

    def parse_conversation(self, jsonl_path: Path) -> List[Dict[str, str]]:
        """Parse a session JSONL file and extract user/assistant messages."""
        messages: List[Dict[str, str]] = []

        try:
            with open(jsonl_path, "r", encoding="utf-8") as file:
                for line in file:
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if data.get("type") != "response_item":
                        continue

                    payload = data.get("payload", {})
                    if not isinstance(payload, dict):
                        continue

                    if payload.get("type") != "message":
                        continue

                    role = payload.get("role")
                    if role not in {"user", "assistant"}:
                        continue

                    text = self._extract_text(payload.get("content"))
                    if not text:
                        continue

                    messages.append(
                        {
                            "role": role,
                            "content": text,
                            "timestamp": data.get("timestamp", ""),
                        }
                    )
        except Exception as error:
            print(f"{Colors.RED}Error reading file: {error}{Colors.END}")
            return []

        return messages

    def display_conversation(self, messages: List[Dict[str, str]], day_label: str, file_name: str) -> None:
        """Display the conversation content in the terminal."""
        self.menu.clear_screen()

        print(f"{Colors.BOLD}{Colors.CYAN}Date: {day_label}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}Session: {file_name}{Colors.END}")
        print("=" * 80)
        print()

        for message in messages:
            role = message["role"]
            content = message["content"]

            if role == "user":
                print(f"{Colors.GREEN}{Colors.BOLD}user:{Colors.END}")
            elif role == "assistant":
                print(f"{Colors.BLUE}{Colors.BOLD}assistant:{Colors.END}")
            else:
                print(f"{Colors.WHITE}{Colors.BOLD}{role}:{Colors.END}")

            print(content)
            print()

        print(f"{Colors.GRAY}Press any key to return to the menu...{Colors.END}")
        self.menu.get_key()

    def run(self) -> None:
        """Run the interactive viewer."""
        while True:
            dates = self.get_dates()
            if not dates:
                print(
                    f"{Colors.RED}No Codex sessions found in {self.sessions_dir}{Colors.END}"
                )
                sys.exit(1)

            date_labels = [label for label, _ in dates]
            paginate_dates = len(date_labels) > 15
            selected_date_idx = self.menu.display_menu(
                date_labels,
                "Select a Date",
                paginate=paginate_dates,
                items_per_page=15,
            )

            day_label, day_path = dates[selected_date_idx]

            while True:
                sessions = self.get_sessions(day_path)
                if not sessions:
                    self.menu.clear_screen()
                    print(
                        f"{Colors.YELLOW}No sessions found for {day_label}{Colors.END}"
                    )
                    print(f"{Colors.GRAY}Press any key to continue...{Colors.END}")
                    self.menu.get_key()
                    break

                session_labels = [label for label, _ in sessions]
                menu_items = ["< Back to Dates"] + session_labels
                paginate_sessions = len(menu_items) > 10
                selected_session_idx = self.menu.display_menu(
                    menu_items,
                    f"Select a Session from {day_label}",
                    paginate=paginate_sessions,
                    items_per_page=10,
                )

                if selected_session_idx == 0:
                    break

                session_path = sessions[selected_session_idx - 1][1]
                messages = self.parse_conversation(session_path)

                if messages:
                    self.display_conversation(messages, day_label, session_path.name)
                else:
                    self.menu.clear_screen()
                    print(
                        f"{Colors.YELLOW}No messages found in this session{Colors.END}"
                    )
                    print(f"{Colors.GRAY}Press any key to continue...{Colors.END}")
                    self.menu.get_key()


def main() -> None:
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in {"--version", "-v"}:
            print(f"cohistory version {VERSION}")
            sys.exit(0)
        if arg in {"--help", "-h"}:
            print("Codex Conversation History Viewer")
            print()
            print("Usage: cohistory")
            print()
            print("Interactive CLI tool to browse Codex conversation history")
            print()
            print("Options:")
            print("  -h, --help     Show this help message")
            print("  -v, --version  Show version information")
            sys.exit(0)

    try:
        viewer = CodexHistoryViewer()
        viewer.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as error:
        print(f"{Colors.RED}Unexpected error: {error}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
