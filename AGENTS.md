# AGENTS.md

## Project overview
- Project: `Auto-Tweet`
- Purpose: fetch recent global news, generate a concise tweet with an LLM, and email the result.
- Runtime: Python 3.11
- Main entrypoint: `generate_tweet.py`
- Supporting module: `send_email.py`
- CI/CD automation: `.github/workflows/auto-tweet.yml` (daily scheduled run + manual trigger)

## Tech stack
- `groq` for chat completion
- `tavily-python` for web search/news gathering
- `python-dotenv` for environment variable loading
- Standard library SMTP (`smtplib`) for email delivery via Gmail

## Local setup
1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Create a `.env` file in repo root with:
   - `GROQ_API_KEY=...`
   - `TAVILY_API_KEY=...`
   - `EMAIL_ADDRESS=...`
   - `EMAIL_APP_PASSWORD=...`

## Run commands
- Generate tweet and send email:
  - `python generate_tweet.py`
- If only email behavior is being tested, call `send_email(...)` from a short Python shell/script.

## Automation behavior
- GitHub Actions workflow: `.github/workflows/auto-tweet.yml`
- Schedule: daily at `03:30 UTC` (`09:00 IST`)
- Also supports manual run via `workflow_dispatch`
- Required GitHub repository secrets:
  - `GROQ_API_KEY`
  - `TAVILY_API_KEY`
  - `EMAIL_ADDRESS`
  - `EMAIL_APP_PASSWORD`

## Code conventions for agents
- Keep edits small and targeted; avoid broad refactors unless requested.
- Preserve existing file structure and script-style entrypoint (`if __name__ == '__main__':`).
- Prefer clear function extraction for new logic instead of adding long inline blocks.
- Add minimal logging/print output only when it improves operability.
- Keep dependencies lean; update `requirements.txt` only when needed.

## Safety and secrets
- Never hardcode credentials, emails, API keys, or app passwords.
- Do not print secrets to logs or workflow output.
- Use environment variables for all credentials.
- Treat `.env` as local-only and keep it out of version control.

## Common tasks
- Update news prompt quality:
  - Edit `query`, `sys_prompt`, or `user_prompt` in `generate_tweet.py`.
- Change model/provider settings:
  - Update Groq model name and completion parameters in `generate_tweet.py`.
- Change email recipient/subject:
  - Adjust `send_email(...)` call in `generate_tweet.py` or make recipient configurable.
- Change run timing:
  - Update cron expression in `.github/workflows/auto-tweet.yml`.

## Validation checklist after edits
- Run `python generate_tweet.py` locally (with valid `.env`) and confirm:
  - Tavily search returns content
  - LLM response is produced
  - Email send succeeds
- If workflow was changed, ensure YAML remains valid and secrets list is still complete.

## Known improvement areas (optional future work)
- Add retries and timeout handling for Tavily/Groq/API failures.
- Add structured logging instead of plain `print`.
- Add unit tests for prompt construction and email helper behavior.
- Externalize prompts/config to a dedicated config file.
