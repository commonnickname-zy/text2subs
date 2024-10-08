import re
import difflib
import argparse
import os
from itertools import takewhile
from adjust_punctuation_ja import adjust_punctuation_ja
from adjust_punctuation_en import adjust_punctuation_en

config = {
    "lang": None,        # Will hold the language code
    "book_format": None  # Will hold the book file extension
}

# Step 1: Extract text from SRT file
# additional automatic cleanup can be performed here
def extract_text_from_srt(srt_file):
    with open(srt_file, 'r', encoding='utf-8') as file:
        srt_content = file.read()

    pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?:\n{2,}|\Z)', re.DOTALL)
    matches = pattern.findall(srt_content)

    # Process matches to construct subtitles list and entire_sub_text
    subtitles = [{'index': i+1, 'timestamp': timestamp, 'text': text.replace('\n', '')} for i, (_, timestamp, text) in enumerate(matches)]
    entire_sub_text = ''.join(sub['text'] for sub in subtitles)

    return subtitles, entire_sub_text

# Step 2: Read the book file
# additional automatic cleanup can be performed here
def read_book_file(book_file):
    # Determine the file extension
    _, file_extension = os.path.splitext(book_file)

    # Set the text_format in config
    config['book_format'] = file_extension.lower()
    
    if file_extension.lower() == '.txt':
        # If it's a .txt file, read and process it as text
        with open(book_file, 'r', encoding='utf-8') as file:
            book_text = file.read()
        book_text = re.sub(r'\n+', '', book_text)  # remove newlines
        return book_text
    elif file_extension.lower() == '.srt':
        # If it's a .srt file, extract text using the extract_text_from_srt function
        _, book_text = extract_text_from_srt(book_file)
        return book_text
    else:
        raise ValueError(f"Unsupported file format {file_extension}. Please provide a .txt or .srt file.")

# Step 3: Generate a diff list
# using the default Python difflib implementation to construct a difference between subtitles and the book
def generate_diff_list(sub_text, book_text):
    matcher = difflib.SequenceMatcher(None, sub_text, book_text)
    diff_list = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        diff_list.append({'subs': sub_text[i1:i2], 'book': book_text[j1:j2], 'sub_segments': set()})
    return diff_list

# recursive longest common subsequence construction
def get_lcs(a: str, b: str, memo={}):
    if not a or not b:
        return ""
        
    if (a, b) in memo:
        return memo[(a, b)]

    head_a, tail_a = a[0], a[1:]
    without_head_a = get_lcs(tail_a, b)
    with_head_a = "" if (f := b.find(head_a)) < 0 else head_a + get_lcs(tail_a, b[f+1:], memo)

    memo[(a, b)] = max([with_head_a, without_head_a], key=len)
        
    return memo[(a, b)]
    
def construct_granular_diff(a: str, b: str):
    lcs = get_lcs(a, b)
    diff = []

    # Initialize the index variables to start at the beginning of a, b, and LCS
    a_index = b_index = lcs_index = 0 

    while lcs_index < len(lcs):
        # Case 1: Characters in 'a' or 'b' do not match the current LCS character.
        if a[a_index] != lcs[lcs_index] or b[b_index] != lcs[lcs_index]:
            a_start, b_start = a_index, b_index
            a_index = next_a if (next_a := a.find(lcs[lcs_index], a_index)) >= 0 else len(a)
            b_index = next_b if (next_b := b.find(lcs[lcs_index], b_index)) >= 0 else len(b)
            diff.append((a[a_start:a_index], b[b_start:b_index]))

        # Case 2: Characters in both 'a' and 'b' match the current LCS character
        overlap = ''.join(_[0] for _ in takewhile(lambda x: x[0] == x[1] == x[2], zip(a[a_index:], b[b_index:], lcs[lcs_index:])))
        length = len(overlap)
        a_index, b_index, lcs_index = a_index+length, b_index+length, lcs_index+length
        
        diff.append((overlap, overlap))  # Add the grouped matching segments

    # Handle remaining characters after the LCS is fully traversed
    if a_index < len(a) or b_index < len(b):
        diff.append((a[a_index:], b[b_index:]))

    return diff
    
# Step 3.5: granulate diffs
def granulate_diff_segments(diff_list):
    granulated_diff_list = []
    for diff in diff_list:
        if diff['subs'] == diff['book']:
            granulated_diff_list.append(diff)
        elif not diff['subs'] or not diff['book']:
            granulated_diff_list.append(diff)
        else:
            granular_diff_list = construct_granular_diff(diff['subs'], diff['book'])
            for granular_diff in granular_diff_list:
                granulated_diff_list.append({'subs':granular_diff[0], 'book':granular_diff[1], 'sub_segments': set()})
        
    return granulated_diff_list
    
# Step 4: Generate a diff list
def write_diff_list_to_file(diff_list, output_diff_file):
    with open(output_diff_file, 'w', encoding='utf-8') as file:
        for diff in diff_list:
            file.write(f"Subs: {diff['subs']}\n")
            file.write(f"Book: {diff['book']}\n")
            file.write(f"Sub Segments: {sorted(list(diff['sub_segments']))}\n")
            file.write("\n")
    
# Step 5: Relate diff segments and subs segments
def map_diff_to_subtitles(diff_list, subtitles):
    diff_index = subs_index = 0
    accumulated_diff = ""
    diff_incremented = True
    
    while subs_index < len(subtitles) and diff_index < len(diff_list):
        if diff_incremented:
            accumulated_diff += diff_list[diff_index]['subs']
            diff_incremented = False
            
        sub = subtitles[subs_index]['text']
        diff_list[diff_index]['sub_segments'].add(subs_index + 1)
        
        found = accumulated_diff.find(sub)
        # increment diff if match not found, or the match exhausts the current diff snippet
        if found < 0:
            diff_index += 1
            diff_incremented = True
        elif found == 0:
        # remove sub snippet from the diff segment
            accumulated_diff = accumulated_diff[len(sub):]
            
            # increment diff if match fully exhausts the current diff snippet
            if len(accumulated_diff) == 0:
                diff_index += 1
                diff_incremented = True

            subs_index += 1
        else:
            print(f"Match found at non-zero index, indicating a misalignment. Sub: {sub}, Diff: {accumulated_diff}")
            break

    return diff_list
     
def split_by_overlap(diff, a: str, b: str):
    # Check for the largest possible overlap
    for i in range(len(a)):
        if a.startswith(b):
            return b, None
        if b.startswith(a[i:]):
            max_overlap = len(a) - i
            # Split b based on the overlap
            return b[:max_overlap], b[max_overlap:]
   
    print(diff)
    print(f"Didn't find overlap: {a}, {b}")
    return None, None
     
# Step 6: Refine diff segments to split them when applicable, according to subs segments
def refine_diff_segments(diff_list, subtitles):
    new_diff_list = []
    for diff in diff_list:
        sub_segments = diff['sub_segments']
        
        # if there's only one sub segment mapping, leave as is
        if len(sub_segments) == 1:
            new_diff_list.append(diff)
        # if it's a diff segment with matching subs-book - have to split appropriately
        elif diff['subs'] == diff['book']:
            diff_text = diff['subs']
            for i in sorted(list(sub_segments)):
                segment_text, diff_text = split_by_overlap(diff, subtitles[i-1]['text'], diff_text)
                new_diff_list.append({'subs': segment_text, 'book': segment_text, 'sub_segments': {i} })
        # non-overlapping subs and book segment. No choice but to assign every sub segment the same content
        else:
            for i in sorted(list(sub_segments)):
                new_diff_list.append({'subs': diff['subs'], 'book': diff['book'], 'sub_segments': {i}})
                
    return new_diff_list

# Step 7: Generate new subtitles
def generate_new_subtitles(mapped_diff_list, srt_subtitles):
    new_subtitles = []

    index = 1
    for sub in srt_subtitles:
        # Combine book text segments from mapped_diff_list
        combined_text = ''
        for diff in mapped_diff_list:
            if sub['index'] in diff['sub_segments']:
                combined_text += diff['book']
        
        if combined_text == "":
            continue 
        # Create new subtitle entry
        new_subtitle = { 'index': index, 'timestamp': sub['timestamp'], 'text': combined_text }
        new_subtitles.append(new_subtitle)
        index += 1

    return new_subtitles

# Step 8: Write new subtitles to file
def write_srt_file(subtitles, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        for sub in subtitles:
            file.write(f"{sub['index']}\n")
            file.write(f"{sub['timestamp']}\n")
            file.write(f"{sub['text']}\n\n")

def main():
    # Map language codes to the corresponding adjustment functions
    lang_to_punctuation_func = {
        'ja': adjust_punctuation_ja,
        'en': adjust_punctuation_en,
    }

    # Create a sorted list of supported language codes and their descriptions
    supported_languages = sorted(lang_to_punctuation_func.keys())
    supported_languages_text = ", ".join(supported_languages)
    epilog_text = f"Supported languages for punctuation adjustment: {supported_languages_text}"

    parser = argparse.ArgumentParser(
        description="Subtitles Synchronization Script",
        epilog=epilog_text
    )
    
    parser.add_argument('subtitle_path', type=str, help="Path to the subtitle file", nargs='?')
    parser.add_argument('text_path', type=str, help="Path to the text file", nargs='?')
    parser.add_argument('output_path', type=str, help="Path to the output file", nargs='?')
    parser.add_argument('--debug', action='store_true', help="Enable debug mode to write intermediate files")
    parser.add_argument('--lang', type=str, help="Specify language for punctuation adjustment")

    args = parser.parse_args()

    # Set the lang in config
    config['lang'] = args.lang
    
    if not args.subtitle_path or not args.text_path or not args.output_path:
        parser.print_help()
        return

    output_filename = os.path.splitext(args.output_path)[0]

    srt_subtitles, entire_sub_text = extract_text_from_srt(args.subtitle_path)
    book_text = read_book_file(args.text_path)

    diff_list = generate_diff_list(entire_sub_text, book_text)
    if args.debug:
        write_diff_list_to_file(diff_list, f'{output_filename}_1_diff.txt')
    
    granulated_diff_list = granulate_diff_segments(diff_list)
    if args.debug:
        write_diff_list_to_file(granulated_diff_list, f'{output_filename}_2_granulated_diff.txt')
    
    mapped_diff_list = map_diff_to_subtitles(granulated_diff_list, srt_subtitles)
    if args.debug:
        write_diff_list_to_file(mapped_diff_list, f'{output_filename}_3_mapped_diff.txt')
    
    refined_diff_segments = refine_diff_segments(mapped_diff_list, srt_subtitles)
    if args.debug:
        write_diff_list_to_file(refined_diff_segments, f'{output_filename}_4_refined_diff.txt')
    
    new_subs = generate_new_subtitles(refined_diff_segments, srt_subtitles)
    if args.lang in lang_to_punctuation_func:
        if args.debug:
            write_srt_file(new_subs, f'{output_filename}_5_new_raw_subs.srt')
        #Step 8 adjust punctionation
        adjusted_subs = lang_to_punctuation_func[args.lang](new_subs, config)
        write_srt_file(adjusted_subs, args.output_path)
    else:
        write_srt_file(new_subs, args.output_path)

if __name__ == "__main__":
    main()

