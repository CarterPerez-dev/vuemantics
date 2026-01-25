"""
ⒸAngelaMos | 2026
prompts.py

Vision model prompts for media analysis
"""


IMAGE_ANALYSIS_PROMPT = """Analyze this image and provide a detailed description that would help someone find it through text search.

Include:
- Main subjects (people, animals, objects)
- Actions or activities
- Setting/location
- Mood or atmosphere
- Notable colors or visual elements
- Any text visible in the image

Be specific and descriptive, using natural language that someone might use to search for this image."""


VIDEO_ANALYSIS_PROMPT = """Analyze these {frame_count} frames from a video and provide a comprehensive description.

Include:
- Main subjects and their actions throughout the video
- Changes or progression between frames
- Setting/location
- Overall theme or story
- Any text or important visual elements
- Mood or atmosphere

Describe it as a cohesive video, not individual frames. Be specific and use natural language that someone might use to search for this video."""
