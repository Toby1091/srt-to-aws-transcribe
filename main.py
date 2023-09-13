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


def load_whisper_json_file():
    with open(input_name + '.json') as f:
        segments = json.load(f)
        return segments


def convert(blocks):

    output = {
        "results": {
            "transcripts": [{
                "transcript": " ".join(block['content'] for block in blocks),
            }],

            "speaker_labels": {
                "speakers": len(set(block['speaker'] for block in blocks)),
                "segments": [{
                    "start_time": block['start_timestamp'],
                    "end_time": block['end_timestamp'],
                    "speaker_label": block['speaker'],
                    "items": [{
                        "start_time": block['start_timestamp'],
                        "end_time": block['end_timestamp'],
                        "speaker_label": block['speaker'],
                    }]
                } for block in blocks]
            },
            "items": [{
                "start_time": block['start_timestamp'],
                "end_time": block['end_timestamp'],
                "alternatives": [{
                    "content": block['content'],
                    "confidence": "1.0",
                }],
                "type": "pronunciation"
            } for block in blocks]
        },
    }

    return output


if __name__ == '__main__':
    input_name = sys.argv[1]
    output_file = sys.argv[2]

    # for block in parse(input_file):
    # print(block)

    converted = convert(list(parse_srt_file(input_name)))
    # with open(output_file, 'w') as f:
    #     f.write(converted)

    json.dump(converted, open(output_file, 'w'), indent=4)
