def adjust_punctuation_en(subtitles, config={}):
    print(config)
    
    # Move punctuation marks to the correct positions for English
    adjusted_subtitles = []

    for i in range(len(subtitles) - 1):
        current_sub = subtitles[i]
        next_sub = subtitles[i + 1]

        # Trim spaces at the ends of the current subtitle
        current_sub['text'] = current_sub['text'].strip()
        next_sub['text'] = next_sub['text'].strip()

        # If the next subtitle starts with a punctuation mark that should be at the end of the current subtitle
        if next_sub['text'] and next_sub['text'][0] in '.,;!?':
            current_sub['text'] += next_sub['text'][0]
            next_sub['text'] = next_sub['text'][1:].lstrip()

        # If the current subtitle ends with an opening quote or bracket
        if current_sub['text'] and current_sub['text'][-1] in '"\'([{':
            next_sub['text'] = current_sub['text'][-1] + ' ' + next_sub['text']
            current_sub['text'] = current_sub['text'][:-1].rstrip()

        # If the current subtitle ends with a hyphen indicating a split word
        if current_sub['text'] and current_sub['text'][-1] == '-':
            current_sub['text'] = current_sub['text'].rstrip('-')
            next_sub['text'] = current_sub['text'].split()[-1] + next_sub['text']

        # Ensure the next subtitle text starts with an uppercase letter if appropriate
        if next_sub['text'] and next_sub['text'][0].isalnum() and not next_sub['text'][0].isupper():
            next_sub['text'] = next_sub['text'][0].upper() + next_sub['text'][1:]

        adjusted_subtitles.append(current_sub)

    # Append the last subtitle as it is
    adjusted_subtitles.append(subtitles[-1])

    return adjusted_subtitles