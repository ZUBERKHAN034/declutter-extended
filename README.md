# DeClutter

DeClutter is a macOS desktop application that automatically organizes your files using customizable rules. It runs quietly in the background, processing files on a schedule so you never have to tidy up manually.

## Features

*   **Rule-Based Automation** — Create rules that run automatically on a configurable interval.
    *   **Sources:** One or more folders to watch, with optional recursive scanning.
    *   **Conditions:** Filter files by name (glob patterns), date (age), size, or file type. Combine conditions with any / all / none logic.
    *   **Actions:** Move, Copy, Delete, Send to Trash, Rename, or Move to subfolder. Supports token-based renaming (`<filename>`, `<folder>`, `<replace:…>`), folder-structure preservation, and configurable duplicate handling (increment name or overwrite).
    *   **Ignore newest:** Optionally skip the N most recent files per folder.
*   **Background Service** — Rules execute on a timer (default every 5 minutes). A system-tray icon provides quick access to the rules window and settings.
*   **Launch at Startup** — Optionally start DeClutter when you log in.
*   **Native macOS Look** — Automatically follows system dark / light mode.

## Use Cases

*   Automatically delete old files in your Downloads folder.
*   Organize Downloads by moving files into subfolders based on type, date, or other criteria.
*   Keep only the N most recent project versions (e.g. FL Studio or Reaper saves) and archive the rest into a subfolder.

## Technical Details

*   **Framework:** PySide6
*   **Database:** SQLite
*   **Platform:** macOS

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.