import os
from arxiv import Search
from serpapi import GoogleSearch  # ensure "google-search-results" package is installed
from youtube_transcript_api import YouTubeTranscriptApi
from backend.deps import init_genai

genai = init_genai()

async def perform_research(topic: str, objectives: list[str]) -> list[dict]:
    results = []

    # 1. Web search via SerpAPI (GoogleSearch from google-search-results)
    google_search = GoogleSearch({
        "q": topic,
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "engine": "google"
    })
    serp_results = google_search.get_dict().get("organic_results", [])[:5]
    for r in serp_results:
        results.append({"source": r.get("link"), "text": r.get("snippet"), "type": "web"})

    # 2. arXiv abstracts
    search_results = Search(query=topic, max_results=3)
    for p in search_results.results():
        results.append({"source": p.entry_id, "text": p.summary, "type": "arxiv"})

    # 3. YouTube transcript via SerpAPI video search
    try:
        video_search = GoogleSearch({
            "search_query": topic + " lecture",  # Adding "lecture" increases chances of finding videos with transcripts
            "api_key": os.getenv("SERPAPI_API_KEY"),
            "engine": "youtube"
        })
        search_response = video_search.get_dict()
        
        # Add debug info to check the structure
        print(f"YouTube search response keys: {search_response.keys()}")
        
        
        if "video_results" in search_response:
            vids = search_response.get("video_results", [])[:3]  # Try more videos
        elif "videos_results" in search_response:
            vids = search_response.get("videos_results", [])[:3]
        else:
            
            video_keys = [k for k in search_response.keys() if "video" in k.lower()]
            vids = search_response.get(video_keys[0], [])[:3] if video_keys else []
        
        print(f"Found {len(vids)} videos to check for transcripts")
        
        for video_data in vids:
            try:
                video_url = video_data.get("link")
                if not video_url:
                    continue
                    
                print(f"Processing video URL: {video_url}")
                
                # extract video ID from URL
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(video_url)
                vid = None
                if parsed.hostname in ["www.youtube.com", "youtube.com"]:
                    vid = parse_qs(parsed.query).get("v", [None])[0]
                elif parsed.hostname == "youtu.be":
                    vid = parsed.path.lstrip("/")
                
                if vid:
                    print(f"Found video ID: {vid}")
                    transcript = YouTubeTranscriptApi.get_transcript(vid)
                    if transcript:
                        joined = " ".join(seg['text'] for seg in transcript)
                        results.append({"source": video_url, "text": joined, "type": "video"})
                        print(f"Successfully added transcript for video: {video_url}")
                        break  # Stop after finding one valid transcript
            except Exception as e:
                print(f"Error processing individual video {video_url}: {str(e)}")
                continue  # Try the next video
    except Exception as e:
        print(f"Error in YouTube search or transcript retrieval: {str(e)}")

    return results