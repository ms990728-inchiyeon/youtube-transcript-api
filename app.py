from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'OK',
        'service': 'YouTube Transcript API by 인치연',
        'endpoints': {
            'POST /transcript': 'Extract YouTube video transcript'
        }
    })

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.get_json(force=True, silent=True) or {}
        url = data.get('url') or data.get('youtubeUrl')
        video_id = data.get('videoId')
        
        # URL에서 비디오 ID 추출
        if not video_id and url:
            patterns = [
                r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
                r'youtu\.be\/([0-9A-Za-z_-]{11})',
                r'embed\/([0-9A-Za-z_-]{11})',
                r'shorts\/([0-9A-Za-z_-]{11})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    video_id = match.group(1)
                    break
        
        if not video_id:
            return jsonify({
                'success': False,
                'error': '올바른 YouTube URL 또는 video ID가 필요합니다'
            }), 400
        
        # 자막 가져오기 (한국어 우선, 없으면 영어)
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            try:
                transcript = transcript_list.find_transcript(['ko'])
                language = 'ko'
            except:
                try:
                    transcript = transcript_list.find_transcript(['en'])
                    language = 'en'
                except:
                    transcript = next(iter(transcript_list))
                    language = transcript.language_code
            
            segments = transcript.fetch()
            full_text = ' '.join([item['text'] for item in segments])
            
            return jsonify({
                'success': True,
                'video_id': video_id,
                'language': language,
                'transcript': full_text,
                'segments': segments,
                'word_count': len(full_text.split()),
                'char_count': len(full_text),
                'processed_by': 'n8n + Render.com'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'자막을 가져올 수 없습니다: {str(e)}'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'서버 오류: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
