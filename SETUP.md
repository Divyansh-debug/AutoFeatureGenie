# Setup Guide

## API Key Configuration

1. Create a `.env` file in the root directory
2. Add your Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

## Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and paste it in your `.env` file

## Security Note

- Never commit your `.env` file to git
- The `.env` file is already in `.gitignore` to prevent accidental commits
- If you accidentally committed an API key, remove it from git history immediately 