# Pronoterm

A fast, minimalist Terminal User Interface (TUI) to access **Pronote** directly from your Linux terminal.

## Features

- **Grades & Averages**: Detailed view of your evaluations with a built-in grade simulator.
- **Timetable**: Clean schedule view showing classes, teachers, and rooms.
- **School Life**: Track absences, tardiness, and disciplinary records.
- **Modern Interface**: Smooth keyboard navigation right inside your terminal.

---

## Prerequisites

- **Python 3.9** or higher
- `git` and `pip` installed on your system

---

## Installation

### 1. Install System Dependencies

**On Debian / Ubuntu / Linux Mint:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
On Arch Linux / Manjaro:

Bash
sudo pacman -S python python-pip git
2. Clone and Set Up the Project
Open your terminal and run the following commands:

Bash
# Clone the repository
git clone [https://github.com/lxeeo772/pronote-tui.git](https://github.com/lxeeo772/pronote-tui.git)
cd pronote-tui

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install required Python libraries
pip install textual pronotepy
(Note: If you have a requirements.txt file, replace the last command with pip install -r requirements.txt)

Usage
Make sure your virtual environment is activated (source venv/bin/activate), then run the main script:

Bash
python3 main.py
