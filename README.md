# 🏫 Agent Garderie

An intelligent AI-powered system for generating and distributing personalized childcare reports to parents via email and WhatsApp.

## 📋 Overview

**Agent Garderie** is a Python-based solution that leverages Large Language Models (LLMs) via LangChain and Groq to automatically generate beautiful, personalized weekly reports for children in daycare/garderies. The system can deliver these reports through multiple channels (email and WhatsApp) to keep parents informed about their child's activities, meals, sleep, mood, and more.

### Key Features

✨ **AI-Powered Report Generation**
- Uses Groq's Llama 3.3-70B model for intelligent report creation
- Generates beautifully formatted HTML reports with customizable styling

📧 **Multi-Channel Distribution**
- Email delivery with HTML support
- WhatsApp integration via TextMeBot API
- Flexible communication channels

🔒 **Secure API Access**
- API key authentication for each daycare facility
- RESTful endpoints for easy integration

🎨 **Customizable Reports**
- Support for daycare branding (logo, colors, slogan)
- Personalized headers and footers
- Gradient styling and custom color schemes

📊 **Data Management**
- CSV-based observation tracking (meals, sleep, mood, activities)
- Parent contact information management
- Multi-garderie support

## 🏗️ Architecture

### Project Structure

```
agent-garderie/
├── agent_api.py           # Flask REST API server
├── my_agent.py            # CLI interactive tool
├── functions.py           # Core functionality & LLM integration
├── requirements.txt       # Python dependencies
├── .gitignore
└── garderies/             # Directory for daycare configurations
    └── {garderie_id}/
        ├── config.json    # Daycare branding & settings
        ├── observations.csv    # Child observation records
        └── parents.csv    # Parent contact information
```

### Components

#### 1. **functions.py** - Core Logic
- `creer_outil_observations()` - Dynamic tool that reads child observation data from CSV
- `creer_executor()` - Initializes the LLM agent with custom prompts
- `generer_prompt_personnalise()` - Creates garderie-specific system prompts
- `envoyer_email()` - SMTP-based email delivery
- `envoyer_whatsapp_textmebot()` - WhatsApp delivery via TextMeBot API
- `obtenir_parent_info()` - Retrieves parent contact details

#### 2. **agent_api.py** - REST API Server
- **POST `/generer_rapport`** - Generate a report for a child
  - Parameters: `garderie_id`, `api_key`, `prenom`
  - Returns: HTML-formatted report

- **POST `/envoyer_rapport`** - Send a report to parent
  - Parameters: `garderie_id`, `api_key`, `prenom`, `canal` (email/whatsapp), `contenu`
  - Returns: Success/error status

#### 3. **my_agent.py** - Interactive CLI
- Interactive menu-driven interface
- Allows selection of daycare and child
- Generates reports and sends via email/WhatsApp
- Perfect for manual operations and testing

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Groq API key (for LLM access)
- SMTP credentials (for email sending)
- TextMeBot API key (for WhatsApp, optional)
- Flask and dependencies

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/medaminejaadari/agent-garderie.git
   cd agent-garderie
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key
   SENDER_EMAIL=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   TEXTMEBOT_API_KEY=your_textmebot_api_key
   PORT=5000
   ```

5. **Create API keys file**
   Create `cles_api.json` at the project root:
   ```json
   {
     "garderie_1": "api_key_1",
     "garderie_2": "api_key_2"
   }
   ```

6. **Set up daycare data structure**
   ```bash
   mkdir -p garderies/garderie_1
   ```

   Create `garderies/garderie_1/config.json`:
   ```json
   {
     "nom": "Garderie Les Petits Étoiles",
     "slogan": "Où l'apprentissage devient jeu",
     "telephone": "01 23 45 67 89",
     "email_expediteur": "contact@garderie.fr",
     "couleur_principale": "#6d28d9",
     "couleur_secondaire": "#c084fc"
   }
   ```

   Create `garderies/garderie_1/observations.csv`:
   ```csv
   prenom,date,repas,sieste_minutes,humeur,activite_principale,remarque
   Liam,2026-06-10,Excellent,45,Joyeuse,Dessin,Très créatif
   ```

   Create `garderies/garderie_1/parents.csv`:
   ```csv
   prenom,email_parent,telephone
   Liam,parent@example.com,+216 12 345 678
   ```

### Usage

#### Option 1: Using the REST API

Start the server:
```bash
python agent_api.py
```

Generate a report:
```bash
curl -X POST http://localhost:5000/generer_rapport \
  -H "Content-Type: application/json" \
  -d '{
    "garderie_id": "garderie_1",
    "api_key": "api_key_1",
    "prenom": "Liam"
  }'
```

Send a report:
```bash
curl -X POST http://localhost:5000/envoyer_rapport \
  -H "Content-Type: application/json" \
  -d '{
    "garderie_id": "garderie_1",
    "api_key": "api_key_1",
    "prenom": "Liam",
    "canal": "email",
    "contenu": "<html>...</html>"
  }'
```

#### Option 2: Using the Interactive CLI

```bash
python my_agent.py
```

Follow the prompts to:
1. Select a daycare
2. Enter a child's first name
3. View the generated report preview
4. Send via email or WhatsApp

## 📋 Dependencies

- **flask** (2.3.3) - Web framework for the REST API
- **flask-cors** (4.0.0) - CORS support for API requests
- **langchain** (0.1.20) - LLM orchestration framework
- **langchain-groq** (0.0.8) - Groq integration for LangChain
- **python-dotenv** (1.0.0) - Environment variable management
- **requests** (2.31.0) - HTTP library for API calls
- **gunicorn** (21.2.0) - Production WSGI server

## 🔐 Security Considerations

- API keys are stored in `cles_api.json` (should be in `.gitignore`)
- Environment variables stored in `.env` (never commit this file)
- SMTP credentials and API keys must be properly secured
- Always use HTTPS in production
- Validate and sanitize all inputs

## 📝 Report Structure

Generated reports include:

- 🏫 Daycare branding header
- 📅 Weekly report title with child's name
- 🍽️ Alimentation (meals and feeding)
- 😴 Sommeil (sleep and rest)
- 😊 Humeur (mood and emotions)
- 🎨 Activités (activities and learning)
- 💡 Conseils (recommendations for parents)
- 👋 Conclusion (personalized closing)

All reports are styled with:
- Responsive HTML/CSS
- Customizable color gradients
- Professional formatting
- Daycare contact information

## 🛠️ Customization

### Personalize Reports

Edit `functions.py`, function `generer_prompt_personnalise()` to:
- Change report structure and sections
- Add custom instructions for the AI
- Modify styling and formatting

### Add More Channels

Extend `functions.py` and `agent_api.py` to support:
- SMS delivery
- Telegram notifications
- Mobile app integration

## 🐛 Troubleshooting

**Email not sending?**
- Verify SMTP credentials in `.env`
- For Gmail: Use "App Password" (not regular password)
- Check firewall/port 587 access

**WhatsApp API errors?**
- Verify TextMeBot API key is valid
- Ensure phone number is in international format (+country_code)
- Check TextMeBot account has credits

**Report not generated?**
- Verify `observations.csv` exists and is properly formatted
- Check child's name matches exactly (case-insensitive)
- Ensure `config.json` is valid JSON

## 📦 Deployment

### Using Gunicorn (Production)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 agent_api:app
```

### Using Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "agent_api:app"]
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

**Medamine Jaadari**
- GitHub: [@medaminejaadari](https://github.com/medaminejaadari)
- Repository: [agent-garderie](https://github.com/medaminejaadari/agent-garderie)

## 🙏 Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Powered by [Groq's Llama 3.3-70B](https://groq.com/)
- Email delivery via SMTP
- WhatsApp integration via [TextMeBot](https://textmebot.com)

---

**Last Updated:** June 2026

For more information or support, please open an issue on GitHub.
