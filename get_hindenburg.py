import urllib.request
import json

# Use the Wikimedia file API to get the direct URL for Hindenburg disaster.jpg
api_url = 'https://commons.wikimedia.org/w/api.py?action=query&prop=imageinfo&iiprop=url&titles=File%3AHindenburg%20disaster.jpg&format=json'
req = urllib.request.Request(api_url, headers={'User-Agent': 'Cluefolio/1.0'})
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read())
        pages = data.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            image_info = page_data.get('imageinfo', [])
            if image_info:
                print(f'Image URL: {image_info[0].get("url")}')
            else:
                print('No image info found')
                print(json.dumps(page_data, indent=2)[:800])
except Exception as e:
    print(f'Error: {e}')