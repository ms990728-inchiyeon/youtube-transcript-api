from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os

app = Flask(__name__)
CORS(app)

def extract_video_id(url_or_id):
    """YouTube URL에서 비디오 ID 추출"""
    if 'youtube.com/watch?v=' in url_or_id:
        return url_or_id.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in url_or_id:
        return url_or_id.split('youtu.be/')[1].split('?')[0]
    elif 'youtube.com/shorts/' in url_or_id:
        return url_or_id.split('shorts/')[1].split('?')[0]
    else:
        return url_or_id

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
        data = request.json
        url = data.get('url') or data.get('youtubeUrl')
        video_id_input = data.get('videoId')
        prefer_language = data.get('language', 'ko')
        
        if not url and not video_id_input:
            return jsonify({
                'success': False,
                'error': 'URL 또는 video ID가 필요합니다'
            }), 400
        
        # 비디오 ID 추출
        video_id = extract_video_id(video_id_input or url)
        
        print(f"📹 비디오 ID: {video_id}")
        print("🔍 자막 검색 중...")
        
        # 인스턴스 생성 (로컬 방식과 동일)
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        
        # 사용 가능한 자막 목록
        available = list(transcript_list)
        
        print(f"✅ 사용 가능한 자막: {len(available)}개")
        
        # 한국어 찾기
        selected = None
        for t in available:
            if t.language_code == prefer_language:
                selected = t
                print(f"📝 {prefer_language} 자막 선택")
                break
        
        # 한국어 없으면 영어
        if not selected:
            for t in available:
                if t.language_code == 'en':
                    selected = t
                    print("📝 영어 자막 선택")
                    break
        
        # 그래도 없으면 첫 번째
        if not selected:
            selected = available[0]
            print(f"📝 {selected.language} 자막 선택")
        
        # 자막 데이터 가져오기
        subtitle_data = selected.fetch()
        
        # 딕셔너리로 변환
        subtitle_list = []
        for entry in subtitle_data:
            subtitle_list.append({
                'start': entry.start,
                'duration': entry.duration,
                'text': entry.text
            })
        
        # 전체 텍스트
        full_text = ' '.join([entry.text for entry in subtitle_data])
        
        print(f"✅ 추출 완료! {len(subtitle_list)}개 구간\n")
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'language': selected.language,
            'language_code': selected.language_code,
            'total_segments': len(subtitle_list),
            'subtitles': subtitle_list,
            'full_text': full_text,
            'word_count': len(full_text.split()),
            'char_count': len(full_text),
            'processed_by': 'n8n + Render.com'
        })
        
    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'자막 추출 실패: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    print("=" * 60)
    print("🚀 YouTube Transcript API 서버 시작!")
    print(f"📍 포트: {port}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
