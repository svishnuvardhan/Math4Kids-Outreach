import smtplib
import pandas as pd
import os
import time
import random  # Fixed: Added missing import
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
DAILY_LIMIT_PER_ACCOUNT = 10
LOG_FILE = "sent_emails_log.txt"
# Adjusted range to cover all 30 batches
BATCH_FILES = [f"India_Schools_Directory_Batch_{i}_50k.csv" for i in range(1, 2)]

# Gather all 5 accounts from GitHub Secrets
ACCOUNTS = []
for i in range(1, 2):
    email = os.getenv(f"EMAIL_{i}")
    password = os.getenv(f"PASS_{i}")
    if email and password:
        ACCOUNTS.append({"email": email, "password": password})

BODY_TEMPLATE = """Dear {school_name},

I am writing to you because, like many educators in {school_name}, your primary teachers likely spend hours every week searching for or manually creating practice worksheets for their students.

I recently came across math4kids.ca, a project designed to simplify this process while keeping students engaged. I thought it might be a valuable, no-cost addition to your school’s resource library.

What makes this platform particularly helpful for the Indian classroom context is its Worksheet Generator. Instead of using generic sheets, teachers can:  
- Customize Difficulty: Instantly switch between Easy, Medium, and Hard levels to match the specific needs of a class or an individual student.  
- Mixed Operations: Generate sheets that mix addition, subtraction, multiplication, and division to test true conceptual understanding.  
- High Volume: Create up to 100 unique questions per sheet and print them directly to PDF for easy distribution.  

Beyond printables, the site offers interactive Digital Flashcards with mixed-mode challenges and a space-themed spelling game, Spelling Star, that uses a cinematic "Space Rescue" story to help kids with literacy.  

The site is entirely free to use and requires no sign-ups or personal data, making it a safe and immediate tool for your teachers to use in the classroom or for homework assignments.

If you find this helpful, please feel free to share the link with your teaching staff: https://www.math4kids.ca

Best regards,
Vishnu Vardhan Reddy
Math4Kids
"""

def get_sent_emails():
    if not os.path.exists(LOG_FILE):
        return set()
    with open(LOG_FILE, "r") as f:
        return set(line.strip() for line in f)

def log_sent_email(email):
    with open(LOG_FILE, "a") as f:
        f.write(email + "\n")

def run_outreach():
    sent_set = get_sent_emails()
    SUBJECTS = [
        "A math resource for your primary teachers",
        "Free worksheet generator for your school",
        "New interactive math tools for {school_name}", # Changed to {} for formatting
        "Helping teachers save time on math worksheets"
    ]
    
    for account in ACCOUNTS:
        print(f"--- Starting outreach for {account['email']} ---")
        count = 0
        try:
            # Use a context manager for the SMTP server for better resource handling
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(account['email'], account['password'])
                
                for file in BATCH_FILES:
                    if count >= DAILY_LIMIT_PER_ACCOUNT: 
                        break
                    if not os.path.exists(file): 
                        continue
                    
                    print(f"Reading {file}...")
                    df = pd.read_csv(file)
                    
                    for _, row in df.iterrows():
                        if count >= DAILY_LIMIT_PER_ACCOUNT: 
                            break
                        
                        target_email = row['Email ID']
                        school_name = row['School Name']
                        
                        if target_email in sent_set or pd.isna(target_email): 
                            continue
                        
                        # Compose Email
                        msg = MIMEMultipart()
                        msg['From'] = account['email']
                        msg['To'] = target_email
                        
                        # Pick a random subject and format it with the school name
                        raw_subject = random.choice(SUBJECTS)
                        msg['Subject'] = raw_subject.format(school_name=school_name)
                        
                        msg.attach(MIMEText(BODY_TEMPLATE.format(school_name=school_name), 'plain'))
                        
                        try:
                            server.send_message(msg)
                            log_sent_email(target_email)
                            sent_set.add(target_email)
                            count += 1
                            print(f"  [{count}] Sent to: {school_name}")
                            time.sleep(2) # Anti-spam delay
                        except Exception as e:
                            print(f"  [!] Error sending to {target_email}: {e}")
            
            print(f"Finished. Sent {count} emails from {account['email']}.")
            
        except Exception as e:
            print(f"Could not connect with {account['email']}: {e}")

if __name__ == "__main__":
    run_outreach()
