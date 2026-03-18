import os
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from zoneinfo import ZoneInfo

CSV_FILE = "SAFE_du_18-03-2026_au_31-12-2026.csv"

SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
FROM_EMAIL = os.environ["FROM_EMAIL"]

TIMEZONE = os.environ.get("TIMEZONE", "Europe/Paris")


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"Date", "to_email", "subject", "message"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le CSV : {missing}")

    # Format attendu dans ton fichier : jj/mm/aaaa
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    if df["Date"].isna().any():
        bad_rows = df[df["Date"].isna()]
        raise ValueError(
            "Certaines dates du CSV sont invalides. "
            f"Lignes concernées : {bad_rows.index.tolist()}"
        )
    return df


def get_today_row(df: pd.DataFrame):
    today = datetime.now(ZoneInfo(TIMEZONE)).date()
    row = df[df["Date"].dt.date == today]

    if row.empty:
        print(f"Aucune ligne trouvée pour la date du jour : {today}")
        return None

    # S'il y a plusieurs lignes pour la même date, on prend la première
    return row.iloc[0]


def send_email(to_email: str, subject: str, html_message: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email

    html_part = MIMEText(html_message, "html", "utf-8")
    msg.attach(html_part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())

    print(f"Email envoyé à {to_email} avec le sujet : {subject}")


def main():
    df = load_csv(CSV_FILE)
    today_row = get_today_row(df)

    if today_row is None:
        return

    to_email = str(today_row["to_email"]).strip()
    subject = str(today_row["subject"]).strip()
    message = str(today_row["message"]).strip()

    if not to_email or not subject or not message:
        raise ValueError("to_email, subject ou message est vide pour la ligne du jour.")

    send_email(to_email, subject, message)


if __name__ == "__main__":
    main()