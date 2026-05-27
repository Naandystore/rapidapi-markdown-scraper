import os
import json
import datetime
import subprocess
import requests

BIRTH_CERTIFICATE_PATH = "birth_certificate.json"
CYCLE_DAYS = 35

def get_current_date():
    return datetime.date.today().isoformat()

def initialize_birth_certificate():
    if not os.path.exists(BIRTH_CERTIFICATE_PATH):
        data = {
            "model_name": "Scrape-to-Markdown API",
            "start_date": get_current_date(),
            "last_check": get_current_date(),
            "pivots_count": 0
        }
        with open(BIRTH_CERTIFICATE_PATH, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Created birth certificate for model: {data['model_name']} on {data['start_date']}")
        return data
    
    with open(BIRTH_CERTIFICATE_PATH, "r") as f:
        return json.load(f)

def check_rapidapi_revenue():
    # RapidAPI Platform API headers for checking developer transaction analytics.
    # The developer needs to supply RAPIDAPI_DEV_KEY in environment variables.
    dev_key = os.getenv("RAPIDAPI_DEV_KEY")
    api_id = os.getenv("RAPIDAPI_API_ID")
    
    if not dev_key or not api_id:
        print("[WARNING] RAPIDAPI_DEV_KEY or RAPIDAPI_API_ID not found in environment variables.")
        print("Defaulting revenue to $0.00 for testing/safety.")
        return 0.0
    
    url = f"https://platform.rapidapi.com/v1/analytics/earnings"
    headers = {
        "X-RapidAPI-Key": dev_key,
        "Accept": "application/json"
    }
    params = {
        "apiId": api_id,
        "period": "30days" # RapidAPI standard billing parameter
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # RapidAPI returns earnings structure
            return float(data.get("earnings", 0.0))
        else:
            print(f"[ERROR] Failed to fetch RapidAPI earnings: {response.status_code} - {response.text}")
            return 0.0
    except Exception as e:
        print(f"[ERROR] RapidAPI connection error: {str(e)}")
        return 0.0

def main():
    cert = initialize_birth_certificate()
    
    # Parse deploy date
    start_date = datetime.date.fromisoformat(cert["start_date"])
    today = datetime.date.today()
    days_running = (today - start_date).days
    
    print(f"Model '{cert['model_name']}' has been running for {days_running} days (Cycle limit: {CYCLE_DAYS} days).")
    
    # Allow command line override to test pivoting immediately
    force_pivot = os.getenv("FORCE_PIVOT") == "true"
    
    if days_running < CYCLE_DAYS and not force_pivot:
        print("Cycle incomplete. No action needed today.")
        return

    print("Running 35-day financial check...")
    revenue = check_rapidapi_revenue()
    
    # Render free tier server costs = $0.0
    server_costs = float(os.getenv("SERVER_COST_USD", "0.0"))
    
    profit = revenue - server_costs
    print(f"Report: Revenue = ${revenue:.2f}, Cost = ${server_costs:.2f}, Profit = ${profit:.2f}")
    
    if profit <= 0 or force_pivot:
        print("Profit target failed. Triggering autonomous business pivot...")
        # Update birth certificate pivot count
        cert["pivots_count"] += 1
        with open(BIRTH_CERTIFICATE_PATH, "w") as f:
            json.dump(cert, f, indent=4)
            
        # Execute pivot script
        try:
            result = subprocess.run(["python", "pivot_model.py"], capture_output=True, text=True, check=True)
            print("Pivot output:")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Pivot execution failed: {e.stderr}")
    else:
        print("Profit check successful! Extending model life for another 35 days.")
        cert["start_date"] = get_current_date()
        cert["last_check"] = get_current_date()
        with open(BIRTH_CERTIFICATE_PATH, "w") as f:
            json.dump(cert, f, indent=4)

if __name__ == "__main__":
    main()
