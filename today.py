import datetime
from dateutil import relativedelta
import requests
import os
import re
from PIL import Image

HEADERS = {'authorization': 'token '+ os.environ['ACCESS_TOKEN']}
USER_NAME = os.environ['USER_NAME']

def image_to_ascii(image_path, width=45):
    try:
        img = Image.open(image_path)
        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio * 0.45) # Adjusted for better fit
        img = img.resize((width, height))
        img = img.convert('L')
        chars = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "." , " "]
        pixels = img.getdata()
        ascii_str = "\n".join("".join(chars[pixels[y*width+x] // 22] for x in range(width)) for y in range(height))
        return ascii_str
    except Exception as e:
        return f"ASCII Error: {e}"

def daily_readme(birthday):
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return f"{diff.years} years, {diff.months} months, {diff.days} days"

def get_stats():
    query = '''
    query($login: String!) {
        user(login: $login) {
            repositories(first: 100, ownerAffiliations: OWNER) {
                totalCount
                edges { node { stargazers { totalCount } } }
            }
            followers { totalCount }
            contributionsCollection { contributionCalendar { totalContributions } }
        }
    }'''
    r = requests.post('https://api.github.com/graphql', json={'query': query, 'variables':{'login': USER_NAME}}, headers=HEADERS)
    res = r.json()
    if 'data' not in res: raise Exception(f"GraphQL Failed: {res}")
    data = res['data']['user']
    stars = sum([edge['node']['stargazers']['totalCount'] for edge in data['repositories']['edges']])
    return {
        'repos': data['repositories']['totalCount'],
        'stars': stars,
        'followers': data['followers']['totalCount'],
        'commits': data['contributionsCollection']['contributionCalendar']['totalContributions']
    }

def update_svg(filename, age, stats, ascii_art):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # FLEXIBLE REGEX: Finds the ID even if other attributes (class, x, y) are present
    content = re.sub(r'(id="ascii_art"[^>]*>).*?(</text>)', f'\\1\n{ascii_art}\\2', content, flags=re.DOTALL)

    updates = [
        ('uptime_data', age),
        ('repo_data', str(stats['repos'])),
        ('star_data', str(stats['stars'])),
        ('commit_data', str(stats['commits'])),
        ('follower_data', str(stats['followers']))
    ]

    for element_id, value in updates:
        content = re.sub(f'(id="{element_id}"[^>]*>).*?(</text>)', f'\\1{value}\\2', content)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    try:
        age = daily_readme(datetime.datetime(2002, 7, 13))
        stats = get_stats()
        print(f"DEBUG: Found stats for {USER_NAME}: {stats}")
        ascii_art = image_to_ascii('profile.jpg')
        update_svg('dark_mode.svg', age, stats, ascii_art)
        update_svg('light_mode.svg', age, stats, ascii_art)
        print("Success: SVGs updated.")
    except Exception as e:
        print(f"Error: {e}")
