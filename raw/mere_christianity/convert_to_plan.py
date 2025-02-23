import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

plan = {
    "name": "Mere Christianity",
    "type": "book",
    "readings": []
}

paragraphs = open('/root/mbrpgabot/raw/mere_christianity/tweaked.txt', 'r').read().split('\n\n')

raw_readings = []
for paragraph in paragraphs:
    text = paragraph.replace('\n', ' ')
    word_count = len(paragraph.split(' '))
    raw_readings.append({
        "text": text,
        "length": len(text),
        "word_count": word_count
    })

reading_text = []
reading_count = 0
while raw_readings:
    raw_reading = raw_readings.pop(0)
    reading_text.append(raw_reading['text'])
    reading_count += raw_reading['word_count']
    
    if reading_count >= 300 or not raw_readings:
        plan['readings'].append(reading_text)
        reading_text = []
        reading_count = 0

json.dump(plan, open('/root/mbrpgabot/plans/mere_christianity.json', 'w'), indent=2)