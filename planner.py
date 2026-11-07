
def plan_task(query: str):
    q = query.lower().strip()

    if q.startswith("play "):
        return {
            "tool": "music_play",
            "query": q.replace("play", "").strip()
            }
    
    if q.startswith("search ") or q.startswith("google "):
        return {
            "tool": "web_search",
            "query": q.replace("search", "").replace("google", "").strip()
            }

    # everything else handled by main handler
    return {
        "tool": "delegate"
        }
