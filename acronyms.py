# http://acronyms.silmaril.ie/cgi-bin/xaa?{query}
# https://www.acronymfinder.com/{query}.html

# Rules for an acronym: 2 or more letters and 1 or fewer vowels. Not a word.

import re
import ast
import requests
from bs4 import BeautifulSoup
import sqlite3

# Load english words
with open('words.txt','r') as file:
    words = set(file.read().split('\n'))

conn = sqlite3.connect('acronym-ratings.db')
c = conn.cursor()

# Create necessary tables if they do not exist
c.execute('''CREATE TABLE IF NOT EXISTS RATINGS ([acronym] TEXT PRIMARY KEY NOT NULL, [delta_rating] integer NOT NULL, [last_updated] date NOT NULL)''')
c.execute('''CREATE TABLE IF NOT EXISTS CACHE ([acronym] TEXT PRIMARY KEY NOT NULL, [acronym_data] text NOT NULL, [cached] date NOT NULL)''')
conn.commit()

def clean_db_num(db:str, date_column_name:str, limit:int=1024):
    c.execute(f'''SELECT COUNT(ALL acronym) FROM {db}''')
    count = c.fetchall()[0][0]
    if count > limit:
        c.execute(f'''DELETE BOTTOM {count-limit} FROM {db} ORDER BY {date_column_name}''')

def clean_db_date(db:str, date_column_name:str, day_limit:int=7):
    c.execute(f'''DELETE FROM {db} WHERE {date_column_name} < date('now','-{day_limit}days')''')

def rate_acr(full_acr:str, delta:int):
    c.execute(f"SELECT * FROM RATINGS WHERE acronym = ?",(full_acr,))
    current_rating = 0

    rows = c.fetchall()
    if len(rows) > 0:
        current_rating = int(rows[0][1])
    
    current_rating += delta    
    
    c.execute('''REPLACE INTO RATINGS VALUES (?, ?,  date('now'))''', (full_acr, current_rating))
    clean_db_date('RATINGS','last_updated')
    conn.commit()

def find_acrs(query):
    clean_db_num('CACHE', 'cached')
    clean_db_date('CACHE','cached')

    # Check for an existing entry    
    c.execute(f"SELECT * FROM CACHE WHERE acronym = ?",(query,))
    rows = c.fetchall()
    if len(rows) > 0:
        return ast.literal_eval(rows[0][1])

    acrs = list()
    URL = f'https://www.acronymfinder.com/{query}.html'
    soup = BeautifulSoup(requests.get(URL).content, 'html.parser')
    parent = soup.find_all(class_="tab-content")
    if len(parent) <= 0: return
    for tr in parent[0].find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) <= 1: continue
        
        child = tds[0].findChildren()[0]
        if 'title' not in child.attrs: continue

        title = child.attrs['title'][3+len(query):]
        rating = int(child.attrs['class'][0][1:])
        cat = ''
        if title.count('(') == 1: title, cat = title.split('(')
        acrs.append((title.strip().title(), rating, cat.replace(')','').strip().lower()))
    
    # Store the newly calculated value
    c.execute('''REPLACE INTO CACHE VALUES (?, ?,  date('now'))''', (query, str(acrs)))
    conn.commit()

    return acrs

def properly_rate_acr(acr_tuple:tuple, favored_cat:str='chat', community_rating_weight:float=0.5):
    assert len(acr_tuple) == 3 and isinstance(acr_tuple[1], int), "Improper acr tuple"
    rating = acr_tuple[1]

    # get community rating from sql
    c.execute(f"SELECT * FROM RATINGS WHERE acronym = ?",(acr_tuple[0],))
    rows = c.fetchall()
    if len(rows) > 0: rating += int(community_rating_weight*rows[0][1])

    # apply multiplier and return
    if len(favored_cat) > 0 and favored_cat.lower() in str(acr_tuple[2]).lower(): rating *= 2
    return (acr_tuple[0], rating, acr_tuple[1])

def find_rated_acrs(query:str):
    clean_db_num('RATINGS', 'last_updated')
    acrs = find_acrs(query)
    acrs = list(sorted(map(properly_rate_acr, acrs), key=lambda t: t[1], reverse=True))
    conn.commit()
    return acrs

def get_possible_acrs(sentence:str):
    possible_acrs = list()
    for word in sentence.split(' '):
        word = re.sub(r'[^\w\s]','',word.strip())
        vowels = word.count('a') + word.count('e') + word.count('i') + word.count('o') + word.count('u') + 0.1 * word.count('y')
        if len(word) > 1 and vowels < len(word) * 0.6 and word.lower() not in words: possible_acrs.append(word)
    return possible_acrs

def find_most_probable_acrs_in_sentence(sentence:str):
    all_acrs = get_possible_acrs(sentence)
    acrs = {query: find_rated_acrs(query)[0][0] for query in all_acrs}
    return acrs

if __name__ == "__main__":
    print(find_rated_acrs('fml'))
    print(find_most_probable_acrs_in_sentence('My teacher just gave hw over xmas. fml.'))