"""
Convert output of whiper-diarization to AWS Transcribe JSON format.

Usage: python main.py <input_name> <output_file>

<input_name>: name of the input file without extension. The script expects a .srt and .json file with the same name.
The srt file should be the output of whisper-diarization. The json file should be the json-serialized segements generated by whipser.

<output_file>: name of the output file.
"""
import sys
import json
from datetime import datetime


def timestamp_to_seconds(timestamp):
    time_format = "%H:%M:%S,%f"
    dt = datetime.strptime(timestamp, time_format)
    total_seconds = (dt.hour * 3600) + (dt.minute * 60) + \
        dt.second + (dt.microsecond / 1000000)
    return total_seconds


def parse_srt_file(input_name):
    with open(input_name + '.srt') as f:
        lines_iter = iter(f)

        try:
            while lines_iter:
                number = next(lines_iter).strip()
                timestamps = next(lines_iter).strip()
                speaker_and_content = next(lines_iter).strip()
                next(lines_iter)  # skip the empty line

                start_timestamp, end_timestamp = timestamps.split(' --> ')
                speaker, content = speaker_and_content.split(': ')

                yield {
                    'start_timestamp': str(timestamp_to_seconds(start_timestamp)),
                    'end_timestamp': str(timestamp_to_seconds(end_timestamp)),
                    'speaker': speaker,
                    'content': content,
                }

        except StopIteration:
            pass


def load_whisper_json_file(input_name):
    with open(input_name + '.json', encoding='utf-8-sig') as f:
        segments = json.load(f)
        # Whisper separates its output into segments. We flatten those segements into one list for easier access.
        flattened_segments = []
        for segment in segments:
            flattened_segments.extend((
                {'start': word[0], 'end': word[1], 'text': word[2]} for word in segment['words']))
        return flattened_segments


def convert(diarized_segments, whisper_words):
    whisper_words_index = 0
    items = []
    speaker_segments = []
    for disarized_segment in diarized_segments:
        diarized_words = disarized_segment['content'].split(' ')
        speaker = disarized_segment['speaker'].replace(' ', '_').lower()

        speaker_start = whisper_words[whisper_words_index]['start']
        speaker_items = []

        for diarized_word in diarized_words:
            whisper_word = whisper_words[whisper_words_index]

            if (whisper_word['text'].strip() != diarized_word.strip()):
                print(
                    f"ERROR: word mismatch. whisper: {repr(whisper_word['text'])}, diarized: {repr(diarized_word)}")

            items.append({
                "start_time": str(whisper_word['start']),
                "end_time": str(whisper_word['end']),
                "alternatives": [{
                    "content": diarized_word,
                    "confidence": "1.0",
                }],
                "type": "pronunciation"
            })

            speaker_items.append({
                "start_time": str(whisper_word['start']),
                "end_time": str(whisper_word['end']),
                "speaker_label": speaker,
            })

            whisper_words_index += 1

        speaker_segments.append({
            "start_time": str(speaker_start),
            "end_time": str(whisper_word['end']),
            "speaker_label": speaker,
            "items": speaker_items,
        })

    output = {
        "results": {
            "transcripts": [{
                "transcript": " ".join(block['content'] for block in diarized_segments),
            }],

            "speaker_labels": {
                "speakers": len(set(block['speaker'] for block in diarized_segments)),
                "segments": speaker_segments,
            },
            "items": items,

        },
    }

    return output


if __name__ == '__main__':
    input_name = sys.argv[1]
    output_file = sys.argv[2]

    whisper_words = load_whisper_json_file(input_name)
    print(whisper_words)
    converted = convert(list(parse_srt_file(input_name)), whisper_words)

    json.dump(converted, open(output_file, 'w'), indent=4)
