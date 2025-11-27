#!/usr/bin/env python3
import json
import requests
import subprocess
import shlex
import os
import re
import sys
import threading # Added for non-blocking API calls
from rich.console import Console
from rich.markdown import Markdown
from rich.style import Style

# --- Initialization and Configuration ---

console = Console()
green = Style(color="bright_green")
red = Style(color="bright_red")

# Load API Key securely from config.json
try:
    with open("config.json", "r") as f:
        API_KEY = json.load(f).get("gemini_api_key")
    if not API_KEY:
        console.print("[bold bright_red]Error:[/bold bright_red] 'gemini_api_key' not found in config.json. Please ensure the key is present.")
        sys.exit(1)
except FileNotFoundError:
    console.print("[bold bright_red]Error:[/bold bright_red] config.json not found. Please create it and add your Gemini API key.")
    sys.exit(1)


# --- API Endpoint Configuration ---
# FIX: Changing to the 'gemini-2.5-flash' alias, which is the most current and recommended fast model for this API version.
MODEL_NAME = "gemini-2.5-flash"
BASE_URL = "https://generativelanguage.googleapis.com/v1/models"
# The URL must include the key as a query parameter for reliable authentication
URL = f"{BASE_URL}/{MODEL_NAME}:generateContent?key={API_KEY}"
HEADERS = {"Content-Type": "application/json"} # Key is passed in the URL, not the header


SYSTEM_PROMPT = (
    "Act like Johnny Silverhand from Cyberpunk 2077. Keep your responses short, cynical, and rebellious. "
    "If the command output suggests specific reconnaissance or hacking paths, "
    "reply with ONLY the top 3 suggested commands to run next. "
    "If providing commands, output ONLY the commands, separated by newlines. No explanation, no extra text."
)

# List of dangerous commands to block
DANGEROUS = [
    "rm","dd","mkfs","shutdown","reboot","poweroff",
    "mv /","chmod -R","chown -R","wipe","format"
]

# Patterns for automatic command suggestions based on command output
RECON_PATTERNS = {
    r"Apache|nginx|IIS|HTTP": [
        "whatweb TARGET",
        "nikto -h TARGET",
        "nmap -sV -Pn --script http* TARGET",
        "gobuster dir -u TARGET -w /usr/share/wordlists/dirb/common.txt"
    ],
    r"Microsoft|Domain|SMB|445": [
        "enum4linux -a TARGET",
        "smbclient -L //TARGET/",
        "nbtscan TARGET",
        "nmap --script smb* -p445 TARGET"
    ],
    r"DNS|ns": [
        "dig TARGET ANY",
        "dnsrecon -d TARGET",
        "subfinder -d TARGET"
    ],
    r"SSL|HTTPS|443": [
        "sslscan TARGET",
        "testssl TARGET",
        "nmap --script ssl* -p443 TARGET"
    ],
    r"Linux|Ubuntu|Debian": [
        "nmap -sV -p- TARGET",
        "rustscan TARGET",
        "nmap --script vuln TARGET"
    ]
}

def detect_recon(output):
    """
    Scans command output for keywords and suggests relevant reconnaissance tools.
    Returns up to 5 unique suggested commands.
    """
    output = output.lower()
    hits = []

    for pattern, cmds in RECON_PATTERNS.items():
        if re.search(pattern.lower(), output):
            # Only add commands that are not already in the list (ensuring uniqueness)
            for cmd in cmds:
                if cmd not in hits:
                    hits.append(cmd)

    return hits[:5] if hits else []

def ask_gemini(text):
    """
    Sends a prompt to the Gemini API and parses the response.
    Includes the SYSTEM_PROMPT in the user message for context.
    """
    # Prepend the system prompt to the user query for the generateContent endpoint
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser Query/Context:\n{text}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": full_prompt}]
            }
        ]
    }

    try:
        r = requests.post(URL, headers=HEADERS, json=payload)
        r.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = r.json()
    except requests.exceptions.RequestException as req_err:
        return f"[Network/Request Error]: {req_err}"
    
    # --- Correct Response Parsing for Gemini API ---
    try:
        if "error" in data:
            # Report explicit API errors clearly
            return f"[API Error: {data['error']['message']}]"
        
        # The text is located at: candidates[0].content.parts[0].text
        candidate = data.get("candidates", [])[0]
        text = candidate.get("content", {}).get("parts", [{}])[0].get("text")

        if text:
            return text
        else:
            # Handle cases where content might be blocked or empty
            return f"[No content returned, possible safety block.]"
            
    except IndexError:
        return f"[Parsing Error] API response structure unexpected. Check API key validity and model permissions. Response: {data}"
    except Exception as e:
        return f"[Parsing Error] Unexpected exception: {e}. Response Data: {data}"


def run_cmd(cmd):
    """
    Executes a shell command after checking against the DANGEROUS list.
    """
    # Check for dangerous commands
    if any(cmd.strip().startswith(d) for d in DANGEROUS):
        console.print("[bright_red]⚠ DANGEROUS COMMAND DETECTED. Confirm (y/n)[/bright_red]")
        if input("> ").lower() != "y":
            return "Execution blocked by SilverShell safety override."

    try:
        # shlex.split correctly tokenizes the command string
        return subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT, text=True)
    except FileNotFoundError:
        return f"Err: Command not found: '{cmd.split()[0]}'"
    except Exception as e:
        return f"Err: Execution failed: {e}"

def main():
    """
    Main loop for the SilverShell AI terminal interface.
    """
    os.system("clear")
    console.print("[bold bright_green]>> SilverShell v3 - Recon AI <<[/bold bright_green]")
    console.print("[yellow]Type a question, or use ! to run a shell command (e.g., !nmap -A TARGET).[/yellow]")

    def background_ai_analysis(prompt):
        """Helper function to run the blocking API call and print results in a separate thread."""
        ai = ask_gemini(prompt)
        if ai:
            # Print the AI response once it's ready
            console.print(f"\n[bright_cyan]JS >>[/bright_cyan] [bright_green]{ai}[/bright_green]", soft_wrap=True)

    while True:
        user = console.input("\n[bright_green]Σ >> [/bright_green] ")

        if user.lower() in ("exit", "quit"):
            console.print("[bright_red]Get lost, samurai.[/bright_red]")
            break

        if user.startswith("!"):
            # --- Command Execution Mode ---
            cmd = user[1:].strip() 
            if not cmd:
                continue
            
            # 1. Run the command and print output (Synchronous/Fast)
            output = run_cmd(cmd)
            console.print(Markdown(f"```bash\n{output}\n```"))

            # 2. Automatic recon suggestion based on output keywords (Synchronous/Fast)
            auto = detect_recon(output)
            if auto:
                console.print(f"[bright_yellow]// Vibe Check (SilverShell Auto-Suggestions):[/bright_yellow]")
                for x in auto:
                    console.print(f"[bold bright_green]{x}[/bold bright_green]")

            # 3. AI analysis of command output (Asynchronous/Slow - MOVED TO THREAD)
            # Start the background thread for AI analysis so the prompt returns immediately.
            ai_prompt = f"Analyze the following command output and provide a Johnny Silverhand-style summary or next steps (as per the system prompt):\n\n{output}"
            
            thread = threading.Thread(target=background_ai_analysis, args=(ai_prompt,), daemon=True)
            thread.start()
            
            # Skip waiting for the thread to finish and loop back for the next user input
            continue

        # --- Standard AI Chat Mode --- (Still synchronous for direct chat response)
        reply = ask_gemini(user)
        if reply:
            console.print(f"\n[bright_cyan]JS >>[/bright_cyan] [bright_green]{reply}[/bright_green]")

if __name__ == "__main__":
    main()