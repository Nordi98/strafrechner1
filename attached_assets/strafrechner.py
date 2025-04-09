from flask import Flask, render_template, request
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
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

    for i in range(1, anzahl_straftaten + 1):
        min_strafe = request.form.get(f"geld_min_{i}")
        max_strafe = request.form.get(f"geld_max_{i}")
        he = request.form.get(f"he_{i}")
        vorstrafen = request.form.get(f"vorstrafen_{i}", "0")

        if min_strafe == "" or min_strafe is None:
            continue

        try:
            min_strafe = float(min_strafe) if min_strafe is not None else 0.0
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
            ersparnis = geld * 0.2 # Ersparnis = 20% des ursprünglichen Betrags
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
    jetzt = datetime.now()
    ende = jetzt + timedelta(minutes=haft_minuten)

    result = {
        "gesamt_geld": round(geldstrafe_gesamt, 2),
        "gesamt_he": round(gesamt_he, 2),
        "haft_min": haft_minuten,
        "haftbeginn": jetzt.strftime("%d.%m.%Y %H:%M"),
        "haftende": ende.strftime("%d.%m.%Y %H:%M"),
        "einzelstrafen": einzelstrafen,
        "anwalt_ersparnis": round(anwalt_ersparnis_gesamt, 2) if anwalt else None,
        "geld_ohne_anwalt": round(geldstrafe_original, 2) if anwalt else None
    }

    return render_template("index.html", result=result, anzahl_straftaten=anzahl_straftaten)

# Glitch benötigt die Anwendung so, dass sie auf den Port 3000 hört
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=3000)





















































