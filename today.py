import datetime
from dateutil import relativedelta
import requests
import os
from lxml import etree

HEADERS = {'authorization': 'token '+ os.environ['ACCESS_TOKEN']}
USER_NAME = os.environ['USER_NAME']

def daily_readme(birthday):
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} {}, {} {}, {} {}'.format(
        diff.years, 'year' + ('s' if diff.years != 1 else ''), 
        diff.months, 'month' + ('s' if diff.months != 1 else ''), 
        diff.days, 'day' + ('s' if diff.days != 1 else ''))

def simple_request(query, variables):
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables':variables}, headers=HEADERS)
    if request.status_code == 200: return request
    raise Exception('Query failed')

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
    request = simple_request(query, {'login': USER_NAME})
    data = request.json()['data']['user']
    stars = sum([edge['node']['stargazers']['totalCount'] for edge in data['repositories']['edges']])
    return {
        'repos': data['repositories']['totalCount'],
        'stars': stars,
        'followers': data['followers']['totalCount'],
        'commits': data['contributionsCollection']['contributionCalendar']['totalContributions']
    }

def svg_overwrite(filename, age, stats):
    tree = etree.parse(filename)
    root = tree.getroot()
    find_and_replace(root, 'uptime_data', age)
    justify_format(root, 'repo_data', stats['repos'], 10)
    justify_format(root, 'star_data', stats['stars'], 10)
    justify_format(root, 'commit_data', stats['commits'], 10)
    justify_format(root, 'follower_data', stats['followers'], 10)
    tree.write(filename, encoding='utf-8', xml_declaration=True)

def justify_format(root, element_id, new_text, length):
    new_text = str(f"{'{:,}'.format(new_text)}")
    find_and_replace(root, element_id, new_text)
    just_len = max(0, length - len(new_text))
    dot_string = ' ' + ('.' * (just_len + 20)) + ' ' 
    find_and_replace(root, f"{element_id}_dots", dot_string)

def find_and_replace(root, element_id, new_text):
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None: element.text = new_text

if __name__ == '__main__':
    age = daily_readme(datetime.datetime(2002, 7, 13))
    stats = get_stats()
    svg_overwrite('dark_mode.svg', age, stats)
    svg_overwrite('light_mode.svg', age, stats)
