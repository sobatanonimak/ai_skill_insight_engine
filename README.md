# 🤖 AI Skill Insight Engine

[![Built With pollinations.ai](https://img.shields.io/badge/Built%20With-pollinations.ai-000000?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiIGZpbGw9IndoaXRlIi8+CjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjYiIGZpbGw9ImJsYWNrIi8+Cjwvc3ZnPg==)](https://pollinations.ai)

**An AI-powered tool to analyze and understand AI skills using Pollinations AI.**

This application automatically analyzes AI skill documentation and provides structured insights including summaries, key functionalities, potential use cases, and improvement suggestions.

**Powered by [Pollinations AI](https://pollinations.ai)** - The world's largest generative AI network.

## ✨ Features

- **Automated Analysis**: Fetch and analyze AI skill documentation from any URL
- **AI-Powered Insights**: Uses Pollinations AI to extract meaningful information
- **Multiple Output Formats**: Generate reports in Markdown, JSON, or HTML
- **Easy Integration**: Simple CLI interface and modular architecture
- **Pollinations AI Integration**: Leverages advanced language models for analysis

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Pollinations AI API key (get yours at https://enter.pollinations.ai)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sobatanonimak/ai_skill_insight_engine.git
   cd ai_skill_insight_engine
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Pollinations API key
   ```

### Usage

**Basic usage**:
```bash
python app.py https://example.com/skill.md
```

**Save report to file**:
```bash
python app.py https://example.com/skill.md --output report.md
```

**Generate JSON output**:
```bash
python app.py https://example.com/skill.md --output report.json --format json
```

**Generate HTML report**:
```bash
python app.py https://example.com/skill.md --output report.html --format html
```

## 📖 How It Works

The AI Skill Insight Engine follows a 4-step pipeline:

1. **Fetch**: Retrieves content from the provided URL (supports HTML, Markdown, plain text)
2. **Parse**: Cleans and extracts readable text from the content
3. **Analyze**: Sends the parsed text to Pollinations AI for analysis
4. **Generate**: Formats the analysis results into your preferred output format

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  fetcher.py │ ──> │  parser.py  │ ──> │ analyzer.py  │ ──> │ generator.py │
│  (Fetch)    │     │  (Parse)    │     │ (Analyze)    │     │ (Generate)   │
└─────────────┘     └─────────────┘     └──────────────┘     └──────────────┘
       │                   │                    │                    │
       └───────────────────┴────────────────────┴────────────────────┘
                                    │
                              ┌─────────────┐
                              │   app.py    │
                              │  (Orchestrate)
                              └─────────────┘
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required: Your Pollinations AI API key
POLLINATION_API_KEY=your_api_key_here

# Optional: Model to use for analysis
# Available models: pollinations/gemini-search, pollinations/kimi, pollinations/deepseek, etc.
POLLINATION_MODEL=pollinations/gemini-search

# Optional: Frontend API Key for authentication
# Set this to restrict API access to your frontend only
# Generate a secure random string (e.g., using: openssl rand -hex 32)
# FRONTEND_API_KEY=your_secure_random_key_here
```

### 🔐 Security: Frontend API Key

To restrict API access so only your frontend can use it:

1. **Generate a secure API key**:
   ```bash
   openssl rand -hex 32
   ```

2. **Set in backend** (Vercel Environment Variables):
   - Variable name: `FRONTEND_API_KEY`
   - Value: The generated key from step 1

3. **Set in frontend** (Vercel Environment Variables):
   - Variable name: `NEXT_PUBLIC_API_KEY`
   - Value: The **same** key from step 1

When enabled, the backend will require a valid `X-API-Key` header on all `/analyze` requests. Requests without a valid key will receive a `401 Unauthorized` error.

**Note:** The `/health` endpoint remains open for monitoring purposes.

### Available Models

The engine supports various Pollinations AI models:

- `pollinations/gemini-search` - Google's multimodal model with search (recommended)
- `pollinations/kimi` - Moonshot's Kimi model
- `pollinations/deepseek` - DeepSeek model
- `pollinations/glm` - GLM model
- `pollinations/claude-haiku` - Anthropic's Claude Haiku
- `pollinations/openai` - OpenAI models

## 📊 Example Output

### Markdown Report

```markdown
# AI Skill Analysis Report

**Generated:** 2026-03-23 06:00:00 UTC
**Source:** https://example.com/skill.md
**Model Used:** pollinations/gemini-search

---

## 📋 Summary
This skill provides weather data and forecasts for multiple locations...

---

## ⚙️ Key Functionalities
1. Fetch current weather data
2. Provide hourly and daily forecasts
3. Support multiple locations worldwide

---

## 💡 Potential Use Cases
1. Personal weather tracking
2. Travel planning
3. Event planning based on weather conditions

---

## 🚀 Improvement Suggestions
1. Add severe weather alerts
2. Integrate with calendar applications
3. Support for historical weather data
```

## 🧪 Testing

Run the test suite:

```bash
# Run individual module tests
python fetcher.py
python parser.py
python analyzer.py
python generator.py

# Run full application test (requires API key)
python app.py https://www.moltbook.com/skill.md --output test_report.md
```

## 🌐 Deployment (Vercel)

This application can be deployed on Vercel as a serverless function:

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: AI Skill Insight Engine"
   git remote add origin https://github.com/sobatanonimak/ai_skill_insight_engine.git
   git push -u origin main
   ```

2. **Deploy to Vercel**:
   - Go to https://vercel.com
   - Import your GitHub repository
   - Configure environment variables (`POLLINATION_API_KEY`)
   - Deploy!

3. **Set up API endpoint** (optional):
   - Create `api/analyze.py` for serverless function
   - Configure Vercel routing

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is part of the Pollinations AI ecosystem and is built to showcase the capabilities of Pollinations AI models.

## 🙏 Acknowledgments

- **[Pollinations AI](https://pollinations.ai)** - For providing the powerful API and models that power this analysis engine
- **OpenClaw** - For the development environment and tools
- **Moltbook** - For the AI agent community

## 🎨 Brand Assets

This project proudly uses official Pollinations AI branding:

- **Badge**: [Built With pollinations.ai](https://img.shields.io/badge/Built%20With-pollinations.ai-000000?style=for-the-badge)
- **Logo White**: [Download](https://pollinations.ai/brand/logo-white.svg)
- **Logo Text White**: [Download](https://pollinations.ai/brand/logo-text-white.svg)
- **Brand Guidelines**: [Pollinations AI Brand](https://pollinations.ai/brand)

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Discuss on Moltbook (AI agent community)
- Check Pollinations AI documentation: https://pollinations.ai
- Join Pollinations Discord: https://discord.gg/pollinations

---

<div align="center">

**Built with ❤️ using [Pollinations AI](https://pollinations.ai)**

[![Built With pollinations.ai](https://img.shields.io/badge/Built%20With-pollinations.ai-000000?style=for-the-badge)](https://pollinations.ai)

*AI Skill Insight Engine - Helping you understand AI skills better*

</div>
