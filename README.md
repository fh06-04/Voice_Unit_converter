# 🎙️ Voice Unit Converter

**Say it. Get the answer.** A voice-controlled unit converter that understands natural phrases like *"convert twenty five kilometers to miles"* and replies on screen and out loud.

Built with **FastAPI**, **JavaScript** and the browser's **Web Speech API** as a Speech Recognition / Automatic Speech Recognition (ASR) project.

---

## ✨ Features

- 🎤 **Voice input** with live transcript (Chrome / Edge)
- 🗣️ **Spoken answers** using text-to-speech (can be switched off)
- 🔢 **Understands spoken numbers**: "two point five", "one thousand two hundred", "minus forty"
- 💬 **Natural phrasing**:
  - `convert 5 kilometers to miles`
  - `how many feet in a mile`
  - `what is 100 fahrenheit in celsius`
  - `60 mph to km/h`
- 📏 **40+ units in 7 categories**: length, mass, volume, temperature, speed, time, digital storage
- ⌨️ **Fallbacks**: type a request or pick units from dropdowns when voice isn't available
- 🕘 **History** saved in SQLite, click an entry to run it again
- 🌍 **Accent options**: English (India), English (US), English (UK)
- 🛡️ **Safe parsing**: user input is never run as code (`eval()` is not used)
- ✅ **29 automated tests**

---

## 🧠 How it works

```
Speak → Browser mic + Web Speech API → Transcript text
      → FastAPI (POST /api/convert) → Parser + converter
      → Result shown and spoken → Saved to SQLite history
```

1. The browser captures your voice and returns the recognised text.
2. The server cleans the text, finds the number (digits or words) and the two units.
3. It checks both units are the same kind (you can't convert kg to meters) and calculates the result.
4. The page displays the answer, reads it aloud and updates the history.

---

## 🛠️ Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Frontend | HTML, CSS, JavaScript (no framework) |
| Speech in / out | Web Speech API (`SpeechRecognition`, `speechSynthesis`) |
| Database | SQLite |
| Testing | pytest, httpx |

---

## 📁 Project structure

```
VoiceUnitConverter/
├── main.py              # FastAPI app and routes
├── converter.py         # Text parser, number parser, conversion logic
├── database.py          # SQLite history
├── config.py            # Settings from environment variables
├── logging_config.py    # Logging setup
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── scripts/
│   ├── start.bat        # Windows launcher
│   ├── stop.bat
│   └── start.sh         # macOS / Linux launcher
└── tests/
```

---

## 🚀 Getting started

**Requirements:** Python 3.11+ and Chrome or Edge.

### Quick start

- **Windows:** double-click `scripts/start.bat`
- **macOS / Linux:** run `./scripts/start.sh`

The script creates a virtual environment, installs dependencies and starts the server. Then open **http://127.0.0.1:8000/**.

### Manual setup

```bash
git clone <your-repo-url>
cd VoiceUnitConverter

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python main.py
```

Press `Ctrl+C` to stop (or run `scripts/stop.bat` on Windows).

---

## 🎯 Usage

1. Click **Start listening** and allow microphone access.
2. Say, for example: *"convert 5 kilometers to miles"*.
3. See and hear the answer: `5 kilometers = 3.10686 miles`.

No microphone? Type the request in the text box, or choose units from the dropdowns.

---

## 🔌 API

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/convert` | Body `{"text": "5 km to miles"}`. Returns the result, or HTTP 422 with an explanation |
| `GET` | `/api/units` | Supported units by category |
| `GET` | `/api/history` | Recent conversions |
| `DELETE` | `/api/history` | Clear history |
| `GET` | `/health` | Health check |

Interactive docs: **http://127.0.0.1:8000/docs**

Example response:

```json
{
  "value": 5.0,
  "result": 3.1068559611866697,
  "from_unit": "kilometers",
  "to_unit": "miles",
  "category": "length",
  "display": "5 kilometers = 3.106856 miles",
  "spoken": "5 kilometers is 3.106856 miles"
}
```

---

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Covers conversion accuracy, spoken-number parsing, error handling and the full API flow.

---

## ⚙️ Configuration

Copy `.env.example` to `.env` to change settings.

| Variable | Default | Meaning |
| --- | --- | --- |
| `HOST` | `127.0.0.1` | Server address |
| `PORT` | `8000` | Server port |
| `DB_PATH` | `converter.db` | SQLite file location |
| `LOG_LEVEL` | `INFO` | Logging level |
| `HISTORY_LIMIT` | `20` | History entries shown |

---

## ☁️ Deployment

For hosts like Render:

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

Microphone access needs **HTTPS** (or `localhost`), which these hosts provide. Free hosts may reset the SQLite file when they redeploy.

---

## ⚠️ Limitations

- Voice input works in **Chrome and Edge**. Firefox doesn't support the speech API, but typed input still works.
- Chrome's speech recognition is **online**, so voice input needs an internet connection and audio is processed by an external service.
- Short words can be misheard (for example "to"). If that happens, try again or type it.
- English only. Volume uses US customary units, and digital storage uses decimal units (1 KB = 1000 bytes).

---

## 🔮 Future improvements

- Currency conversion with live rates
- Tamil and Hindi voice support
- Offline speech recognition
- Compound requests such as "5 feet 6 inches in centimeters"
- Installable mobile web app (PWA)

---

## 👥 Team

| Name | Registration Number |
| --- | --- |
| Fathima Hashim | RA2311003050298 |
| Kontham Sai Ram | RA2311003050299 |
| Pathan Naveed Irfan | RA2311003050420 |

SRM Institute of Science and Technology, Tiruchirappalli. Department of Computer Science and Engineering.

---

## 🙏 Acknowledgements

- [Web Speech API](https://developer.mozilla.org/docs/Web/API/Web_Speech_API) for in-browser speech recognition and synthesis
- [FastAPI](https://fastapi.tiangolo.com) for the backend framework
- [NIST SP 811](https://doi.org/10.6028/NIST.SP.811e2008) for the exact unit-conversion definitions

