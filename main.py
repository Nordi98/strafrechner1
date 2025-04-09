
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
from datetime import timezone
import pytz
import json
import os

app = Flask(__name__)

def log_change(title, description, changes):
    changelog_file = "changelog.json"
    changelog = []
    if os.path.exists(changelog_file):
        with open(changelog_file, "r") as f:
            changelog = json.load(f)
    
    changelog.insert(0, {
        "timestamp": datetime.now(pytz.timezone('Europe/Berlin')).strftime("%d.%m.%Y %H:%M"),
        "title": title,
        "description": description,
        "changes": changes
    })
    
    with open(changelog_file, "w") as f:
        json.dump(changelog, f)

# Initial changelog entry
if not os.path.exists("changelog.json"):
    log_change(
        "System Start",
        "Strafrechner System initialisiert",
        ["Grundfunktionen implementiert", "Benutzeroberfläche erstellt"]
    )

@app.route("/", methods=["GET", "POST"])
def index():
    current_time = datetime.now()
    try:
        anzahl_straftaten = int(request.form.get("anzahl_straftaten", 1))
    except ValueError:
        anzahl_straftaten = 1

    geldstrafe_gesamt = 0
    gesamt_he = 0
    einzelstrafen = []
    anwalt_ersparnis_gesamt = 0  # Ersparnis durch Anwalt
    geldstrafe_original = 0      # Geldstrafe ohne Anwalt

    kooperativ = request.form.get("kooperativ", "nein") == "ja"
    anwalt = request.form.get("anwalt", "nein") == "ja"
    zahlen = request.form.get("zahlen", "ja") == "ja"
    vorsatz = request.form.get("vorsatz", "nein") == "ja"

    # Verwende die vom Formular übermittelte Anzahl
    try:
        anzahl_straftaten = int(request.form.get("anzahl_straftaten", 1))
    except ValueError:
        anzahl_straftaten = 1

    for i in range(1, anzahl_straftaten + 1):
        min_strafe = request.form.get(f"geld_min_{i}")
        max_strafe = request.form.get(f"geld_max_{i}")
        he = request.form.get(f"he_{i}")
        vorstrafen = request.form.get(f"vorstrafen_{i}", "0")

        if min_strafe == "" or min_strafe is None:
            continue

        try:
            min_strafe = float(min_strafe)
            max_strafe = float(max_strafe) if max_strafe and max_strafe != "" else min_strafe
            he = float(he) if he else 0.0
            vorstrafen = int(vorstrafen) if vorstrafen else 0
        except ValueError:
            min_strafe = 0.0
            max_strafe = 0.0
            he = 0.0
            vorstrafen = 0

        if kooperativ and vorstrafen == 0:
            geld = min_strafe
        else:
            faktor = 1.0 + (0.1 * vorstrafen)
            geld = min_strafe * faktor
            if vorsatz:
                geld *= 1.2
            geld = min(geld, max_strafe)

        geld = round(geld, 2)
        geldstrafe_original += geld  # Geld vor Anwalt speichern

        if anwalt:
            ersparnis = geld * 0.2  # Ersparnis = 20% des ursprünglichen Betrags
            geld *= 0.8
            anwalt_ersparnis_gesamt += ersparnis

        geld = round(geld, 2)
        geldstrafe_gesamt += geld

        haft_aus_geld = geld / 1000 if not zahlen else 0
        gesamt_he += he + haft_aus_geld

        einzelstrafen.append({
            "geldstrafe": f"{geld} $" if zahlen else f"{geld} $ (nicht gezahlt)",
            "haft": round(he + haft_aus_geld, 2)
        })

    haft_minuten = int(gesamt_he * 60)
    ende = current_time + timedelta(minutes=haft_minuten)

    result = {
        "gesamt_geld": round(geldstrafe_gesamt, 2),
        "gesamt_he": round(gesamt_he, 2),
        "haft_min": haft_minuten,
        "haftbeginn": current_time.strftime("%d.%m.%Y %H:%M"),
        "haftende": ende.strftime("%d.%m.%Y %H:%M"),
        "einzelstrafen": einzelstrafen,
        "anwalt_ersparnis": round(anwalt_ersparnis_gesamt, 2) if anwalt else None,
        "geld_ohne_anwalt": round(geldstrafe_original, 2) if anwalt else None
    }

    # Statistik nur bei POST-Request (Formular-Submission) speichern
    if result and request.method == "POST":
        stats_file = "stats.json"
        stats = []
        if os.path.exists(stats_file):
            with open(stats_file, "r") as f:
                stats = json.load(f)
        
        stats.append({
            "zeitpunkt": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "geldstrafe": result["gesamt_geld"],
            "haftzeit": result["haft_min"],
            "kooperativ": request.form.get("kooperativ") == "ja",
            "anwalt": request.form.get("anwalt") == "ja",
            "bezahlt": request.form.get("zahlen") == "ja"
        })
        
        with open(stats_file, "w") as f:
            json.dump(stats, f)

    return render_template("index.html", result=result, anzahl_straftaten=anzahl_straftaten)

@app.route("/statistics")
def statistics():
    stats = []
    if os.path.exists("stats.json"):
        with open("stats.json", "r") as f:
            stats = json.load(f)
    
    total_cases = len(stats)
    total_money = sum(s["geldstrafe"] for s in stats)
    total_jail_time = sum(s["haftzeit"] for s in stats)
    cooperative_cases = sum(1 for s in stats if s["kooperativ"])
    lawyer_cases = sum(1 for s in stats if s["anwalt"])
    paid_cases = sum(1 for s in stats if s["bezahlt"])
    
    return render_template("statistics.html", 
        stats=stats[-10:],  # Letzte 10 Fälle
        total_cases=total_cases,
        total_money=total_money,
        total_jail_time=total_jail_time,
        cooperative_cases=cooperative_cases,
        lawyer_cases=lawyer_cases,
        paid_cases=paid_cases
    )

@app.route("/changelog")
def changelog():
    changelog = []
    if os.path.exists("changelog.json"):
        with open("changelog.json", "r") as f:
            changelog = json.load(f)
    return render_template("changelog.html", changelog=changelog)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
