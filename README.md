<img width="1890" height="948" alt="Screenshot (85)" src="https://github.com/user-attachments/assets/6b38c052-e205-447c-b168-635a54873ec4" />


```markdown
 Mehfooz – AI for Flood & Glacial Lake Outburst (GLOF) Early Warning

> Pakistan has over 7,000 glaciers—the most outside the poles. When they melt, they form dangerous glacial lakes that can burst (GLOF), wiping out entire villages. Mehfooz uses AI to detect these risks early and send life-saving alerts in local languages.

---

 🚀 Project Overview
<img width="1920" height="1080" alt="Screenshot (79)" src="https://github.com/user-attachments/assets/672927cd-539c-4d6b-8616-f1fd5fef545a" />

Mehfooz is an AI-powered early warning system that analyzes daily satellite images of glacial lakes to detect potential Glacial Lake Outburst Floods (GLOFs) and downstream flooding.

Why this matters:
- Pakistan has 7,000+ glaciers
- Rapid melting creates dangerous glacial lakes
- GLOFs wipe out entire villages in Gilgit-Baltistan and Khyber Pakhtunkhwa
- Floods then trigger destruction in Punjab and Sindh
- Current warning systems are slow, manual, and not available in local languages
![Uploading Screenshot (78).png…]()

How Mehfooz solves it:
1. Analyzes satellite images using Qwen-VL (vision AI)
2. Detects three key risk indicators:
   - Lake surface area expansion (swelling)
   - New water channels forming near ice dams
   - Snowmelt acceleration patterns
3. Generates alerts in Urdu, Sindhi, and Pashto
4. Sends GPS-tagged SMS warnings to NDMA, PDMA, and local committees
5. Suggests evacuation routes to high-ground villages

---
<img width="1785" height="943" alt="Screenshot (79)" src="https://github.com/user-attachments/assets/ae3a6247-b7f8-456d-ac82-510e147a7746" />

 🛠️ Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| Vision-Language Model | Qwen-VL (DashScope / Transformers) | Satellite image analysis |
| Satellite Data | Sentinel Hub (Copernicus Data Space) | Free, daily satellite imagery |
| Backend | Python (FastAPI) + Node.js | API orchestration |
| SMS Alerts | Twilio API | Send GPS-tagged warnings |
| Voice Alerts | Google Text-to-Speech | Generate Urdu/Sindhi/Pashto alerts |
| Translation | Google Translate / IndicTrans | Convert alerts into local languages |
| Deployment | Alibaba Cloud (ECS) | Cloud hosting (optional) |

---

 📋 Prerequisites

Before you begin, make sure you have:

- Python 3.9+ installed
- Node.js 16+ installed
- A GitHub account (optional, for hosting code)
- Accounts for the services below (free tiers available)

---

 🔑 API Keys Required

You will need API keys for the following services:

| Service | Purpose | Where to Get It | Cost |
| :--- | :--- | :--- | :--- |
| Sentinel Hub | Satellite imagery | [dataspace.copernicus.eu](https://dataspace.copernicus.eu) | Free |
| Qwen-VL (DashScope) | AI vision analysis | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com) | Pay-as-you-go |
| Google Cloud | Translation + TTS | [console.cloud.google.com](https://console.cloud.google.com) | Free tier |
| Twilio | SMS alerts | [twilio.com](https://twilio.com) | Pay-as-you-go |

---

 ⚙️ Installation

 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mehfooz.git
cd mehfooz
```

 2. Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate   On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

 3. Set Up Node.js Environment

```bash
npm install
```

 4. Create Environment Variables

Create a `.env` file in the root directory:

```env
 Sentinel Hub (Satellite Imagery)
SH_CLIENT_ID=sh-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SH_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

 Qwen-VL (DashScope API)
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

 Google Cloud (Translation + TTS)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

 Twilio (SMS Alerts)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

 Optional: Enable mock mode for demo
MOCK_MODE=true
```

 5. Run the Application

```bash
 Start the backend (Python)
python app/main.py

 Start the frontend (if applicable)
npm start
```

---

 🗺️ Architecture Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Satellite Data │────▶│  Qwen-VL Model  │────▶│  Risk Assessment│
│  (Sentinel/     │     │  (Image         │     │  (Lake Area,    │
│   Landsat)      │     │   Analysis)     │     │   Channels,     │
└─────────────────┘     └─────────────────┘     │   Snowmelt)     │
                                                 └────────┬────────┘
                                                          │
                                                 ┌────────▼────────┐
                                                 │  Alert Pipeline │
                                                 │  (Voice + SMS)  │
                                                 └────────┬────────┘
                                                          │
                                                 ┌────────▼────────┐
                                                 │  Notification  │
                                                 │  (NDMA, PDMA,  │
                                                 │   Local Com.)  │
                                                 └─────────────────┘
```

---

 📁 Project Structure

```
mehfooz/
├── app/
│   ├── main.py               FastAPI backend
│   ├── satellite_ingest.py   Sentinel Hub data ingestion
│   ├── qwen_analyzer.py      Qwen-VL image analysis
│   ├── alert_generator.py    Alert generation (SMS + Voice)
│   ├── translation.py        Language translation (Google/IndicTrans)
│   └── config.py             Configuration and environment variables
├── frontend/                 (Optional) React/Vue dashboard
├── data/                     Local data storage
├── notebooks/                Jupyter notebooks for experimentation
├── .env                      Environment variables
├── requirements.txt          Python dependencies
├── package.json              Node.js dependencies
└── README.md                 This file
```

---

 🚀 Deployment (Alibaba Cloud)

To deploy Mehfooz on Alibaba Cloud:

1. Create an ECS instance (Ubuntu 20.04+)
2. Install dependencies: `Python`, `Node.js`, `Docker`
3. Copy the project files
4. Build and run with Docker:

```bash
docker build -t mehfooz .
docker run -p 80:8000 mehfooz
```

---

 🧪 Running in Demo Mode

For testing without live API keys, enable `MOCK_MODE=true` in your `.env` file.

Demo workflow:
1. Loads sample satellite images from `data/samples/`
2. Simulates Qwen-VL analysis
3. Generates mock alerts in Urdu/Sindhi/Pashto
4. Prints alerts to console (no SMS sent)

---

 👥 Team

| Role | Name |
| :--- | :--- |
| Developer & Presenter | Samra Safdar |

---

 📝 License

This project is open-source and available under the MIT License.

---

 🙏 Acknowledgments

- Alibaba Cloud – Qoder tools and hackathon support
- Alkhidmat Foundation – Hackathon organization
- Bano Qabil Pakistan – Program platform
- Copernicus Data Space Ecosystem – Free satellite imagery

---

 📧 Contact

- Email: samrasdra@gmail.com
- Portfolio: https://samraportfolio.netlify.app/
- LinkedIn: https://www.linkedin.com/in/samra-safdar-16833b30b

---

 ⚡ Quick Commands

| Action | Command |
| :--- | :--- |
| Install dependencies | `pip install -r requirements.txt && npm install` |
| Run backend | `python app/main.py` |
| Run in demo mode | `MOCK_MODE=true python app/main.py` |
| Run with Docker | `docker build -t mehfooz . && docker run -p 80:8000 mehfooz` |

---

 🔄 Continuous Improvement

- [ ] Add real-time satellite data streaming
- [ ] Integrate more language support (Balochi, etc.)
- [ ] Expand to flood and wildfire detection
- [ ] Improve evacuation route optimization
- [ ] Build mobile app for local communities

---

Built with ❤️ for Pakistan's future.
```

---

 What This README Does

| Section | Purpose |
| :--- | :--- |
| Project Overview | Explains the problem and solution |
| Tech Stack | Lists all technologies used |
| Prerequisites | Tells users what they need to start |
| API Keys | Shows where to get each key |
| Installation | Step-by-step setup instructions |
| Architecture Flow | Visual representation of the system |
| Project Structure | Explains the folder layout |
| Deployment | How to deploy on Alibaba Cloud |
| Demo Mode | How to test without live APIs |
| Quick Commands | Handy command reference |

---

 What to Do Now

| Step | Action |
| :--- | :--- |
| 1 | Create a new file called `README.md` in your project root. |
| 2 | Copy-paste the content above into it. |
| 3 | Replace `https://github.com/yourusername/mehfooz.git` with your actual GitHub repo URL. |
| 4 | Commit and push to GitHub. |

---

