import pandas as pd
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

CSV_FILE = "results.csv"

def send_report():
    if not os.path.exists(CSV_FILE):
        print("No data file found.")
        return

    # 1. Calculate Stats
    df = pd.read_csv(CSV_FILE)
    total_draws = len(df)
    
    df['Scraped At'] = pd.to_datetime(df['Scraped At'])
    yesterday = datetime.now() - timedelta(days=1)
    new_draws_count = len(df[df['Scraped At'] > yesterday])

    # 2. Build the Email
    msg = EmailMessage()
    msg['Subject'] = f"Keno Update: {new_draws_count} New Draws Today"
    msg['From'] = os.environ.get('EMAIL_ADDRESS')
    msg['To'] = os.environ.get('EMAIL_ADDRESS') # Sending it to yourself
    
    msg.set_content(f"""
    Hello! 
    
    Here is your daily Keno scraping update:
    - New Draws collected in the last 24h: {new_draws_count}
    - Total Draws in your dataset: {total_draws}
    
    The robot is still working hard.
    """)

    # 3. Send via Gmail SMTP
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.environ.get('EMAIL_ADDRESS'), os.environ.get('EMAIL_PASSWORD'))
            smtp.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    send_report()
