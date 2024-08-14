import re

def adjust_punctuation_ja(subtitles, config={}):
    print(config)
    
    # Process the special character "➡" if the book format was .srt
    if config['book_format'] == '.srt':
        for i, current_sub in enumerate(subtitles):
            # Case 1: "➡" between two non-empty strings
            current_sub['text'] = re.sub(r'(?<=\S)➡(?=\S)', '　', current_sub['text'])

            # Case 2: "➡" at the beginning of the line
            if current_sub['text'].startswith('➡'):
                if i > 0:
                    subtitles[i - 1]['text'] += '➡'
                current_sub['text'] = current_sub['text'][1:].strip()

            # Case 3: "➡" at the end of the line
            current_sub['text'] = current_sub['text'].strip()
            
    # Move punctuation marks to the correct positions for Japanese
    adjusted_subtitles = []

    for i, current_sub in enumerate(subtitles[:-1]):
        next_sub = subtitles[i + 1]

        # Move these characters to the end of the current subtitle
        if next_sub['text'] and next_sub['text'][0] in '）｝］】」』〟。、！？':
            current_sub['text'] += next_sub['text'][0]
            next_sub['text'] = next_sub['text'][1:]

        # Move these characters to the beginning of the next subtitle
        if current_sub['text'] and current_sub['text'][-1] in '（｛［【「『〝':
            next_sub['text'] = current_sub['text'][-1] + next_sub['text']
            current_sub['text'] = current_sub['text'][:-1]

        # Ensure the current subtitle text is trimmed properly
        current_sub['text'] = current_sub['text'].strip()
        next_sub['text'] = next_sub['text'].strip()

        adjusted_subtitles.append(current_sub)

    # Append the last subtitle as it is
    adjusted_subtitles.append(subtitles[-1])

    return adjusted_subtitles