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
        # Resize to fit the terminal area
        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio * 0.5) # 0.5 to account for font height
        img = img.resize((width, height))
        img = img.convert('L') # Grayscale

        # Characters used for shading (Andrew Grant style)
        chars = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "." , " "]
        pixels = img.getdata()
        ascii_str = ""
        for i, pixel in enumerate(pixels):
            if i % width == 0 and i != 0:
                ascii_str += "\n"
            ascii_str += chars[pixel // 22]
        return ascii_str
    except Exception as e:
        print(f"ASCII Error: {e}")
        return " (Image Error) "

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
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables':{'login': USER_NAME}}, headers=HEADERS)
    data = request.json()['data']['user']
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

    # Inject ASCII Art
    content = re.sub(r'id="ascii_art">.*?</text>', f'id="ascii_art">{ascii_art}</text>', content, flags=re.DOTALL)

    # Update Stats
    updates = [
        ('uptime_data', age, 18),
        ('repo_data', str(stats['repos']), 22),
        ('star_data', str(stats['stars']), 22),
        ('commit_data', str(stats['commits']), 20),
        ('follower_data', str(stats['followers']), 16)
    ]

    for element_id, value, dot_length in updates:
        content = re.sub(f'id="{element_id}">.*?<', f'id="{element_id}">{value}<', content)
        just_len = max(0, dot_length - len(value))
        dot_string = ' ' + ('.' * (just_len + 5)) + ' '
        content = re.sub(f'id="{element_id}_dots">.*?<', f'id="{element_id}_dots">{dot_string}<', content)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    age = daily_readme(datetime.datetime(2002, 7, 13))
    stats = get_stats()
    ascii_art = image_to_ascii('profile.jpg')
    update_svg('dark_mode.svg', age, stats, ascii_art)
    update_svg('light_mode.svg', age, stats, ascii_art)
