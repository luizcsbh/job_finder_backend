import time
import httpx
from datetime import datetime, timedelta
from src.infrastructure.storage import get_storage

# Sources to monitor
SOURCES = {
    "Remotive":    "https://remotive.com/api/remote-jobs",
    "ArbeitNow":   "https://www.arbeitnow.com/api/job-board-api",
    "The Muse":    "https://www.themuse.com/api/public/jobs?page=0",
    "Jooble":      "http://jooble.org/",
    "JobIceCream": "https://jobicecream.com/api/jobs?page=1",
    "LinkedIn":    "https://jsearch.p.rapidapi.com/search",
    "OpenAI":      "https://api.openai.com/v1/models",
    "Supabase":    "DB_PING"
}

def perform_health_checks():
    storage = get_storage()
    results = []
    
    for name, url in SOURCES.items():
        status = "offline"
        latency = 0
        try:
            start_time = time.time()
            if url == "DB_PING":
                # Test connection to the primary database table
                storage.client.table("users").select("id").limit(1).execute()
                latency = int((time.time() - start_time) * 1000)
                status = "ok" if latency < 30000 else "warning"
            else:
                try:
                    # Use a timeout slightly above 30s to detect "warning" vs "offline"
                    with httpx.Client(timeout=40.0, follow_redirects=True) as client:
                        # For health checks, a HEAD request is lighter, but some APIs block it
                        # We use GET with a small limit if possible or just the root
                        response = client.get(url)
                        latency = int((time.time() - start_time) * 1000)
                        
                        if latency > 30000:
                            status = "warning"
                        elif response.status_code < 500: # 401/403 often means online but unauthorized
                            status = "ok"
                        else:
                            status = "offline"
                except httpx.TimeoutException:
                    # If it timed out at 40s, it's definitely over 30s, but here we consider it offline if it hangs too long
                    status = "offline"
                except Exception:
                    status = "offline"
        except Exception:
            status = "offline"
            
        health_entry = {
            "api_name": name,
            "status": status,
            "latency_ms": latency
        }
        
        # Save or Update in Supabase api_health table
        try:
            storage.client.table("api_health").upsert({
                "api_name": name,
                "status": status,
                "latency_ms": latency,
                "last_check": datetime.utcnow().isoformat()
            }, on_conflict="api_name").execute()
        except Exception as e:
            print(f"Failed to save health for {name}: {e}")
            
        results.append(health_entry)
        
    return results

def get_system_health():
    """Returns cached health or triggers a fresh check if 5 hours have passed."""
    storage = get_storage()
    try:
        # Check current data
        res = storage.client.table("api_health").select("*").execute()
        data = res.data
        
        if not data:
            return perform_health_checks()
            
        # Parse last check time
        # We assume all entries were updated roughly at the same time
        last_str = data[0]["last_check"]
        # Handle different timestamp formats from postgres
        last_check = datetime.fromisoformat(last_str.replace('Z', '+00:00'))
        
        if datetime.now(last_check.tzinfo) - last_check > timedelta(hours=5):
            return perform_health_checks()
            
        return data
    except Exception as e:
        print(f"Health retrieval error: {e}")
        return perform_health_checks()
