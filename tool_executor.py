from executor import execute_command
from config import find_app_by_capability, app_registry
import yt_dlp
from memory.song_cache import load_cache, save_cache

def run_tool(step: dict) -> str:
    tool = step["tool"]

    if tool == "web_search":
        query = step["query"]
        open_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

        app = find_app_by_capability("web_search")
        if not app:
            return "No browser found."

        chrome_path = app_registry[app]["windows"][0]
        result = execute_command([chrome_path, open_url])

        if result["success"]:
            return f"Searching for {query}"
        return result.get("stderr", "Error opening browser.")

    if tool == "music_play":
        song = step["query"]
        # open_url = f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
        ydl_opts = {
            "quiet": True,
            "skip_download": True
        }
        cache = load_cache()
        try:
            if song.strip().lower() in cache:
                video_url = cache[song]
            else:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(f"ytsearch:{song}", download=False)
                    if "entries" not in result or not result["entries"]:
                        return "Could not find the song"
                
                    video = result["entries"][0]
                    video_url = video["webpage_url"]
                    
                    cache[song] = video_url
                    save_cache(cache)
                
        except Exception as e:
            return f"Search error: {e}"
        
        app = find_app_by_capability("music_play")
        if not app:
            return "No browser found."

        chrome_path = app_registry[app]["windows"][0]
        result = execute_command([chrome_path, video_url])

        if result["success"]:
            return f"🎵 Playing {video['title']}"

        return result.get("stderr", "Error playing music.")
    
    
    if tool == "compute":
        from search_manager import safe_calculate
        expr = step["expression"]
        return str(safe_calculate(expr))

    return "Unknown tool."
