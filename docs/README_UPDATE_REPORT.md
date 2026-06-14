# README Update Report

## Date: June 15, 2026

## Changes Made

### Removed
- All AWS Bedrock references
- All Claude/Anthropic references
- Mock LLM mode documentation (system now uses Gemini live)
- Outdated tech stack entries (boto3, botocore)
- Old architecture diagram referencing Bedrock

### Added
- Google Gemini 2.5 Flash as the AI provider
- Voice Commerce section (Web Speech API + TTS)
- Conversational Commerce flow diagram
- Action command detection explanation
- Checkout flow documentation
- Order management (persistent orders)
- Sustainability dashboard details
- Carbon impact insights
- All 15 frontend pages listed
- API endpoints for Orders (POST, GET)
- Environment variable: `GEMINI_API_KEY`
- Hackathon Highlights table
- Future Improvements section

### Updated
- Tech stack reflects actual dependencies
- Architecture diagram shows current flow (Gemini, not Bedrock)
- Installation commands match actual project structure
- API endpoints section includes all current routes
- Project structure matches actual filesystem
- Badges updated (Google Gemini instead of AWS)

## Verification
- No references to: Bedrock, Claude, anthropic, boto3, AWS SDK
- All tech versions match package.json/requirements.txt
- Folder structure matches actual filesystem
- API endpoints match registered routes in main.py
- Environment variables match .env.example
