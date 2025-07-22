# കേരള പഞ്ചാംഗം ജ്യോതിഷനില സഹിതം (Malayalam Calendar with astrological skymap)


<p>
  <img src="screenshot1.png" width="25%" style="border:1px solid #eee" alt="Malayalam Panchangam showing കർക്കിടകം 07 with thithi/nakshatra">
  <img src="screenshot2.png" width="25%" style="border:1px solid #eee" alt="Real-time astrological chart with graha positions in rashis">
</p>

**Accurate Malayalam calendar for Mac with astrological calculations following traditional Bharatiya timekeeping (06:30 AM = 00:00)**

## 🌟 Features

### Panchangam Display
- കൃഷ്ണവർഷ സൗരമാസ തിയ്യതി (e.g., `5127 കർക്കിടകം 07`)
- Today's complete details:
  - വാരം (Weekday)
  - തിഥി (Moon Phase) with end time
  - നക്ഷത്ര (Star) with end time
- Astrological Sky Map (explained below)
- Month view with Malayalam/Gregorian dates

### Astrological Sky Map
- Real-time celestial chart using Swiss Ephemeris (swisseph)
- Current ലഗ്ന (Ascendant) position
- Planetary positions in Rashis including രാഹു & കേതു
- Traditional Bharatiya time system (Christian Time - 6h30m)
- ((If you want to permanently start using Hindu time, use "Cape Verde (Praia)" as system timezone))


## ⏳ Time System Explained
We follow the **traditional Bharatiya astrological time** where:
- `00:00` = Sunrise (06:30 AM local time)
- `12:00` = Sunset (~06:30 PM)
- Night begins at next `12:01`

*Example:* App shows `13:30` → Actual time is 8:00 PM

## 📥 Installation

### For Regular Users:
1. Download the latest `.app` file from the folder that says [Move the file within to applications folder]
2. Drag to your `/Applications` folder
3. Right-click → Open (to bypass Gatekeeper on first launch)

### For Developers:
1. Use git clone
2. Point the python to your venv (top line of python file). Existing line is my system specific. Python file is located as /Panchangam/scripts/solar_calendar.48m.py
3. Use xcode to archive and create the same file.

### ⚙️ Startup Configuration
To launch automatically at login: 
System Settings → General → Login Items --> Click "+" and select Panchangam.app

### 🤝 Contributions and Feedbacks are welcome

## 📜 License - GNU Affero General Public License v3.0
[![AGPL-3.0](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0) 
- പകർപ്പവകാശം - കൃഷ്ണവർഷം 5127, ശ്രീരാം പോഴത് മേനോൻ (Copyright (C) AD 2025,  Sreeram Pozhat Menon)
- സമ്പർക്കം - sreeram@pozhat.com
