SilverShell v3 - Recon AI Terminal

A Cyberpunk-Inspired AI-Powered Terminal for Reconnaissance and Command Analysis.

SilverShell is a Python-based terminal application that combines shell command execution with the conversational intelligence of the Gemini API. It analyzes command output, suggests next steps, and provides commentary in the cynical, rebellious voice of Johnny Silverhand.

✨ Key Features

AI Command Analysis: Uses the Gemini API to instantly analyze output from local shell commands (e.g., nmap, whoami, ls).

Johnny Silverhand Persona: All AI responses are filtered through a system prompt to maintain a consistent, in-character persona.

Non-Blocking Analysis: AI analysis is executed in a background thread, ensuring the terminal prompt returns immediately after a shell command is run, improving responsiveness.

Automatic Reconnaissance Suggestions: Detects keywords in command output (e.g., "Apache," "SMB," "445") and automatically suggests relevant tools/commands to run next.

Danger Check: Prompts the user for confirmation before executing potentially dangerous system commands (rm, reboot, etc.).

Rich Terminal Output: Uses the rich library for high-contrast, stylized console output.

🚀 Setup

1. Prerequisites

You need Python 3.8+ and the following libraries:

pip install requests rich


2. API Key Configuration (Crucial)

To use the AI features, you must provide a Gemini API Key.

Security Note: For local use, you can use a file. NEVER COMMIT YOUR API KEY TO GIT/GITHUB.

Get a Gemini API Key from Google AI Studio.

Create a file named config.json in the same directory as silvershell.py.

Add your API key to the file in the following format:

{
  "gemini_api_key": "AIzaSyD_RYO6kEy4KHehZKAOV2D1OvHORdUPMBo" 
}


3. Execution

Run the script directly from your terminal:

python3 silvershell.py


⌨️ Usage

1. Execute Shell Commands

Prefix any command with ! to run it directly in your local shell. The output will be displayed, followed by auto-suggestions and the asynchronous AI analysis.

Σ >> !whoami


2. Chat with Johnny

Type any question or comment directly (without the !) to chat with the Johnny Silverhand persona.

Σ >> What do you think about the state of cyber warfare today?


3. Exit

Σ >> exit


⚠️ Security Warning

DO NOT publicly share your config.json file. It contains your private API key. If sharing the project on GitHub, you should:

Add config.json to your .gitignore file.

Consider changing the API key loading logic in silvershell.py to load the key from an environment variable (os.environ.get("GEMINI_API_KEY")) instead of a file for better security.
