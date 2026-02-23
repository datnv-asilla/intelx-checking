import requests
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
INTELX_API_ROOT = "https://free.intelx.io"  # Free tier API endpoint
HISTORY_FILE = "intelx_history.json"
DATABASE_FILE = "database.json"

# Load single API key from environment variable
INTELX_API_KEY = os.getenv('INTELX_API_KEY', '')
if not INTELX_API_KEY:
    raise ValueError("INTELX_API_KEY not found in .env file")

class IntelXAPI:
    """IntelX API Client based on official SDK"""
    
    def __init__(self, api_key, base_url=None):
        self.api_key = api_key
        self.base_url = base_url or INTELX_API_ROOT
        self.headers = {
            'x-key': self.api_key,
            'User-Agent': 'Asilla-IntelX-Scanner/1.0'
        }
        self.timeout = 30
        self.rate_limit = 1  # seconds between requests
    
    def _post(self, endpoint, json_data=None):
        """POST request to IntelX API"""
        url = f"{self.base_url}{endpoint}"
        time.sleep(self.rate_limit)
        
        try:
            response = requests.post(url, json=json_data, headers=self.headers, timeout=self.timeout)
            return response
        except Exception as e:
            print(f"[-] POST Error: {type(e).__name__}: {e}")
            return None
    
    def _get(self, endpoint, params=None):
        """GET request to IntelX API"""
        url = f"{self.base_url}{endpoint}"
        time.sleep(self.rate_limit)
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            return response
        except Exception as e:
            print(f"[-] GET Error: {e}")
            return None
    
    def intelligent_search(self, term, maxresults=100, buckets=[], timeout=5, 
                          datefrom="", dateto="", sort=4, media=0, terminate=[]):
        """
        Initialize an intelligent search and return the search ID
        
        Args:
            term: Search term (domain, email, IP, etc.)
            maxresults: Maximum results per bucket
            timeout: Search timeout in seconds
            sort: Sort order (4 = newest first)
        
        Returns:
            search_id (str) or error code (int)
        """
        payload = {
            "term": term,
            "buckets": buckets,
            "lookuplevel": 0,
            "maxresults": maxresults,
            "timeout": timeout,
            "datefrom": datefrom,
            "dateto": dateto,
            "sort": sort,
            "media": media,
            "terminate": terminate
        }
        
        print(f"[+] Searching for: {term}")
        response = self._post('/intelligent/search', json_data=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 0:
                search_id = data.get('id')
                print(f"[+] Search ID: {search_id}")
                return search_id
            else:
                print(f"[-] Search status error: {data.get('status')}")
                print(f"[-] Response: {data}")
                return None
        elif response.status_code == 401:
            print(f"[-] Error 401: Invalid API key")
            return 401
        elif response.status_code == 402:
            print(f"[-] Error 402: Payment required / Quota exceeded")
            return 402
        elif response.status_code == 429:
            print(f"[-] Error 429: Rate limit exceeded")
            return 429
        else:
            print(f"[-] HTTP Error {response.status_code}")
            try:
                print(f"[-] Response body: {response.text[:200]}")
            except:
                pass
            return response.status_code
    
    def intelligent_search_result(self, search_id, limit=100):
        """
        Get results from an intelligent search
        
        Args:
            search_id: The search ID from intelligent_search()
            limit: Maximum number of results to return
        
        Returns:
            dict with 'status' and 'records', or error code
        """
        if not search_id:
            return None
        
        params = {
            "id": search_id,
            "limit": limit
        }
        
        print("[+] Getting search results...")
        response = self._get('/intelligent/search/result', params=params)
        
        if not response:
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[-] Error getting results: {response.status_code}")
            return response.status_code
    
    def get_statistics(self, search_id):
        """
        Get statistics for a search (bucket counts)
        
        Returns:
            dict with media statistics
        """
        if not search_id:
            return None
        
        # Wait a bit for results to aggregate
        time.sleep(2)
        
        # Get results and calculate statistics
        result = self.intelligent_search_result(search_id, limit=1000)
        
        if not result or isinstance(result, int):
            return None
        
        # Calculate statistics from records
        stats = {}
        records = result.get('records', [])
        
        for record in records:
            bucket = record.get('bucket', 'unknown')
            if bucket in stats:
                stats[bucket] += 1
            else:
                stats[bucket] = 1
        
        # Convert to media format for compatibility
        media_stats = []
        for bucket, count in stats.items():
            media_stats.append({
                'mediah': bucket,
                'count': count
            })
        
        return {'media': media_stats, 'total': len(records)}

def send_slack(data):
    """Send message to Slack"""
    SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID", "C0A21V42A64")
    ENDPOINT = "https://slack.com/api/chat.postMessage"
    SLACK_TOKEN = os.environ.get("SLACK_TOKEN")

    payload = {
        'channel': SLACK_CHANNEL_ID,
        'text': data
    }
    
    headers = {
        'Content-Type': 'application/json;charset=utf-8',
        'Authorization': f"Bearer {SLACK_TOKEN}"
    }

    try:
        response = requests.post(
            ENDPOINT,
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        print("[+] Message sent to Slack successfully")
    except Exception as e:
        print(f"[-] Error sending to Slack: {e}")


def load_history():
    """Load previous scan history"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_history(history):
    """Save scan history to file"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"[-] Error saving history: {e}")


def load_progress():
    """Load progress file to track completed URLs"""
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, 'r') as f:
                data = json.load(f)
                # Ensure both fields exist
                if 'LIST_CHECK_URL' not in data:
                    data['LIST_CHECK_URL'] = []
                if 'done_check_urls' not in data:
                    data['done_check_urls'] = []
                return data
        except:
            return {'LIST_CHECK_URL': [], 'done_check_urls': []}
    return {'LIST_CHECK_URL': [], 'done_check_urls': []}


def save_progress(progress):
    """Save progress to file"""
    try:
        with open(DATABASE_FILE, 'w') as f:
            json.dump(progress, f, indent=2)
        total_urls = len(progress.get('LIST_CHECK_URL', []))
        done_urls = len(progress.get('done_check_urls', []))
        print(f"[+] Progress saved: {done_urls}/{total_urls} URLs completed")
    except Exception as e:
        print(f"[-] Error saving progress: {e}")


def reset_progress():
    """Reset progress when all URLs are checked"""
    progress = load_progress()
    progress['done_check_urls'] = []
    save_progress(progress)
    print("[+] Progress reset - starting new cycle")
    return progress


def compare_results(url, current_stats, previous_stats):
    """
    Compare current stats with previous stats
    
    Returns:
        tuple: (comparison_message, has_changes, is_first_scan)
    """
    # First time scan (never scanned before)
    if previous_stats is None:
        return "🆕 First time scan", True, True
    
    # Previous scan had no data, now we have data
    if len(previous_stats) == 0 and len(current_stats) > 0:
        summary = ', '.join([f"{item['count']} {item['mediah']}" for item in current_stats])
        return f"⚠️ NEW DATA FOUND!\n📊 {summary}", True, False
    
    # Previous scan had data, now we have no data (handled separately)
    if len(previous_stats) > 0 and len(current_stats) == 0:
        return "✅ All data removed", True, False
    
    changes = []
    current_dict = {item['mediah']: item['count'] for item in current_stats}
    previous_dict = {item['mediah']: item['count'] for item in previous_stats}
    
    # Check for increases
    for media_type, count in current_dict.items():
        prev_count = previous_dict.get(media_type, 0)
        if count > prev_count:
            diff = count - prev_count
            changes.append(f"📈 {media_type}: +{diff} (was {prev_count}, now {count})")
    
    # Check for decreases
    for media_type, prev_count in previous_dict.items():
        count = current_dict.get(media_type, 0)
        if count < prev_count:
            diff = prev_count - count
            changes.append(f"📉 {media_type}: -{diff} (was {prev_count}, now {count})")
    
    # Check for new types
    for media_type in current_dict:
        if media_type not in previous_dict:
            changes.append(f"🆕 New type: {media_type} ({current_dict[media_type]})")
    
    # Check for removed types
    for media_type in previous_dict:
        if media_type not in current_dict:
            changes.append(f"❌ Removed: {media_type} (was {previous_dict[media_type]})")
    
    if changes:
        return "\n".join(changes), True, False
    else:
        return "✅ No changes detected", False, False


if __name__ == "__main__":
    check_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    history = load_history()
    progress = load_progress()
    current_scan = {}  # Will be saved at the end
    
    # Get LIST_CHECK_URL from database.json
    LIST_CHECK_URL = progress.get('LIST_CHECK_URL', [])
    if not LIST_CHECK_URL:
        raise ValueError("LIST_CHECK_URL not found in database.json")
    
    # Get list of URLs that need to be checked
    done_urls = set(progress.get('done_check_urls', []))
    remaining_urls = [url for url in LIST_CHECK_URL if url not in done_urls]
    
    # If all URLs are done, reset and start new cycle
    if not remaining_urls:
        print("[+] All URLs completed in previous cycle. Starting new cycle...")
        progress = reset_progress()
        done_urls = set(progress.get('done_check_urls', []))  # Update done_urls after reset
        remaining_urls = LIST_CHECK_URL.copy()
    
    print(f"[+] Total URLs to check: {len(LIST_CHECK_URL)}")
    print(f"[+] Already checked: {len(done_urls)}")
    print(f"[+] Remaining: {len(remaining_urls)}")
    print(f"[+] Will scan up to 50 URLs today\n")
    
    # Initialize IntelX API client
    api = IntelXAPI(INTELX_API_KEY)
    
    # Track changes for summary
    urls_with_changes = 0
    urls_checked = 0
    max_daily_checks = 50  # Free tier limit
    
    for url in remaining_urls:
        # Stop if reached daily limit
        if urls_checked >= max_daily_checks:
            print(f"\n[!] Reached daily limit of {max_daily_checks} checks")
            print(f"[!] Will continue tomorrow with remaining {len(remaining_urls) - urls_checked} URLs")
            break
        
        print(f"\n{'='*60}")
        print(f"[+] Check Date: {check_date}")
        print(f"[+] Progress: {len(done_urls) + urls_checked + 1}/{len(LIST_CHECK_URL)}")
        print(f"[+] Checking URL: {url}")
        print(f"{'='*60}")
        
        # Search using API
        search_id = api.intelligent_search(url, maxresults=100, timeout=5, sort=4)
        
        # Handle API errors
        if isinstance(search_id, int):
            if search_id == 402:
                print(f"[!] API key quota exceeded (402)")
                print(f"[!] Checked {urls_checked} URLs today. Will continue tomorrow.")
                break
            elif search_id == 429:
                print(f"[!] Rate limit exceeded (429). Waiting 60 seconds...")
                time.sleep(60)
                search_id = api.intelligent_search(url, maxresults=100, timeout=5, sort=4)
                if isinstance(search_id, int):
                    print(f"[-] Still rate limited. Skipping for now.")
                    continue
            elif search_id == 401:
                print(f"[!] Invalid API key (401). Please check your .env file.")
                break
            else:
                print(f"[-] Search failed with error code: {search_id}")
                continue
        
        if search_id and not isinstance(search_id, int):
            urls_checked += 1
            
            # Get statistics using API
            stats = api.get_statistics(search_id)
            if stats:
                media_stats = stats.get('media', [])
                
                # Save current scan data (even if empty)
                if not media_stats:
                    # No data found - save empty state
                    current_scan[url] = {
                        'date': check_date,
                        'media': []
                    }
                    print(f"\n[+] URL: {url}")
                    print(f"[+] Status: No data found")
                    print(f"[✓] Saved empty state - skipped Slack notification")
                else:
                    # Get previous stats before updating
                    previous_stats = history.get(url, {}).get('media', None)
                    
                    # Save current scan data (with data) to current_scan
                    current_scan[url] = {
                        'date': check_date,
                        'media': media_stats
                    }
                    
                    # Compare with previous scan
                    comparison, has_changes, is_first_scan = compare_results(url, media_stats, previous_stats)
                    
                    # Always print to console
                    print(f"\n[+] URL: {url}")
                    current_data = ', '.join([f"{item['count']} {item['mediah']}" for item in media_stats])
                    print(f"[+] Current data: {current_data}")
                    print(f"[+] Status: {comparison}")
                    
                    # Only send to Slack if there are changes
                    if has_changes:
                        urls_with_changes += 1
                        if is_first_scan:
                            summary_parts = [f"{item['count']} {item['mediah']}" 
                                           for item in media_stats 
                                           if item.get('count', 0) > 0 and item.get('mediah', '')]
                            
                            result_message = f"*🔍 IntelX Alert - {check_date}*\n"
                            result_message += f"URL: `{url}`\n"
                            result_message += f"📊 Found: {', '.join(summary_parts)}\n"
                            result_message += f"Status: {comparison}"
                        else:
                            result_message = f"*⚠️ IntelX Change Detected - {check_date}*\n"
                            result_message += f"URL: `{url}`\n"
                            result_message += f"{comparison}"
                        
                        send_slack(result_message)
                        print("[✓] Changes detected - sent to Slack")
                    else:
                        print("[✓] No changes - skipped Slack notification")
            else:
                print("[-] Could not get statistics")
            
            # Mark URL as done and save progress
            progress['done_check_urls'].append(url)
            save_progress(progress)
        else:
            print(f"[-] Search failed (search_id: {search_id})")
        
        # Sleep between requests to avoid rate limiting
        time.sleep(2)
    
    # Merge current scan into history and save once
    if current_scan:
        history.update(current_scan)
        save_history(history)
        print(f"[+] Updated history with {len(current_scan)} URLs")
    
    # Send daily summary to Slack
    print(f"\n[✔] Done! Checked {urls_checked} URLs today")
    print(f"[✔] History saved to {HISTORY_FILE}")
    print(f"[✔] Progress: {len(progress['done_check_urls'])}/{len(LIST_CHECK_URL)} total")
    
    # Build and send summary message
    summary_message = f"*✅ IntelX Daily Scan - {check_date}*\n"
    summary_message += f"📊 Checked today: {urls_checked} URLs\n"
    summary_message += f"📈 Progress: {len(progress['done_check_urls'])}/{len(LIST_CHECK_URL)} total\n"
    
    if urls_with_changes > 0:
        summary_message += f"⚠️ Changes detected: {urls_with_changes} URL(s)\n"
        summary_message += f"_Check above messages for details_"
    else:
        summary_message += f"✅ No changes detected\n"
        summary_message += f"_All checked URLs are stable_"
    
    # Check if cycle is complete
    if len(progress['done_check_urls']) >= len(LIST_CHECK_URL):
        summary_message += f"\n\n🎉 *Cycle Complete!* All {len(LIST_CHECK_URL)} URLs checked. Will reset tomorrow."
    
    send_slack(summary_message)
    print("[✓] Daily summary sent to Slack")
