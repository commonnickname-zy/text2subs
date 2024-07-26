# text2subs
### A tool to synchronize generated subtitles and accurate content from human-verified text.

Suppose you have a piece of video or audio media and need accurate subtitles, both in terms of timing and the content. You're able to generate subtitles automatically (for example, [whisper](https://github.com/openai/whisper)), which takes care of timing, but the content can contain some inaccuracies. Luckily, you have a human-verified transcript, or the source book in case of an audiobook etc. - but it's not formatted as subtitles.

This tool allows you to take the timing of the automated subtitles, and align the text to create subtitles that are accurate both in terms of timing and content.

## Features

- Extracts text from SRT subtitle files.
- Reads and processes human-verified transcripts or source texts.
- Generates a diff list to identify differences between automated subtitles and human-verified text.
- Aligns and maps the human-verified text to the timing of the automated subtitles.
- Supports punctuation adjustments for multiple languages (currently Japanese and English).
- Provides debug mode to output intermediate processing steps.

## Requirements

- Python 3.x
- A way to automatically generate subtitles from audio
- Accurate text source

## Usage

   ```Python
   python text2subs.py path/to/subtitles.srt path/to/book.txt path/to/output.srt --debug --lang=ja
   ```
Debug and lang argument are optional, though lang is recommended when the target language is supported.
Note that cleaning up the input files manually is not required, but it will help to make the result more accurate. For example, there might be se significant differences between a text and an audio version of the book in the beginning, and deleting the intro segments may prove helpful.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## TODO

- Support for .epub text source
- Support for more languages
- Improved performance
  
