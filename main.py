import base64
from datetime import datetime
import os
import feedparser
import google.generativeai as genai
import requests  # 워드프레스 REST API 통신용 라이브러리

# 1. API 키 및 설정 (GitHub Secret에서 안전하게 가져옵니다)
api_key = os.environ.get("GEMINI_API_KEY")

# 이메일 관련 변수 (현재는 주석 처리되었지만 추후 필요시 사용)
# sender_email = os.environ.get("MY_EMAIL")
# email_password = os.environ.get("EMAIL_PASSWORD")
# receiver_email = os.environ.get("RECEIVER_EMAIL")

# 워드프레스 연동 정보 설정 (GitHub Secret에서 가져옴)
WP_SITE_URL = os.environ.get("WP_SITE_URL")
WP_USER = os.environ.get("WP_USER")
WP_PASSWORD = os.environ.get("WP_PASSWORD")

if not api_key:
  raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다!")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-3.5-flash")  # 안정적인 모델 버전으로 설정


def get_bmw_news():
  print("🚗 BMW 최신 뉴스를 수집하는 중...")
  rss_url = "https://news.google.com/rss/search?q=BMW&hl=ko&gl=KR&ceid=KR:ko"
  feed = feedparser.parse(rss_url)

  news_list = []
  for entry in feed.entries[:3]:
    news_list.append(f"제목: {entry.title}\n링크: {entry.link}\n")

  return "\n".join(news_list)


def summarize_news(news_text):
  print("🤖 Gemini AI가 뉴스를 요약하는 중...")
  prompt = f"""
    다음은 최근 BMW 관련 뉴스 목록입니다. 
    이 내용들을 바탕으로 주요 뉴스 5가지를 요약해서 워드프레스 블로그용으로 만들어주세요.

    [뉴스 원본]
    {news_text}
    """
  response = model.generate_content(prompt)
  return response.text


# [주석 처리] 기존 GitHub Pages용 HTML 파일 생성 함수 (사용 안 함)
# def save_to_html(summary_text):
#     ...


# [주석 처리] 기존 이메일 발송 함수 (사용 안 함)
# def send_email(summary_text):
#     ...


# [신규 추가] 워드프레스 자동 포스팅 함수
def post_to_wordpress(title, summary_text):
  print("📝 워드프레스에 포스팅을 전송하는 중...")

  if not WP_SITE_URL or not WP_USER or not WP_PASSWORD:
    print("⚠️ 워드프레스 설정(Secret)이 누락되어 포스팅을 건너뜁니다.")
    return

  api_url = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

  # Basic Auth 인증 헤더 생성
  credentials = f"{WP_USER}:{WP_PASSWORD}"
  token = base64.b64encode(credentials.encode()).decode()
  headers = {
      "Authorization": f"Basic {token}",
      "Content-Type": "application/json",
  }

  # 본문 줄바꿈을 HTML 태그(<br>)로 변환하여 가독성 높이기
  formatted_content = summary_text.replace("\n", "<br>")

  # 전송할 데이터 구조 (status를 'publish'로 하면 즉시 발행, 'draft'로 하면 임시글 저장)
  data = {
      "title": title,
      "content": formatted_content,
      "status": "publish",
  }

  try:
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 201:
      print("✅ 성공적으로 워드프레스에 포스팅되었습니다!")
    else:
      print(f"❌ 워드프레스 포스팅 실패: {response.status_code}, {response.text}")
  except Exception as e:
    print(f"❌ 워드프레스 통신 중 오류 발생: {e}")


if __name__ == "__main__":
  news_data = get_bmw_news()
  if not news_data:
    print("수집된 뉴스가 없습니다.")
  else:
    summary = summarize_news(news_data)
    print("\n" + "=" * 40)
    print("✨ [BMW 뉴스 요약 결과]")
    print("=" * 40)
    print(summary)

    # 포스팅 제목 생성 (오늘 날짜 포함)
    today_date = datetime.now().strftime("%Y년 %m월 %d일")
    post_title = f"🚗 BMW Daily News Briefing ({today_date})"

    # 1. 기존 블로그 HTML 파일 저장 (주석 처리)
    # save_to_html(summary)

    # 2. 기존 이메일 발송 (주석 처리)
    # send_email(summary)

    # 3. 워드프레스 포스팅 실행
    post_to_wordpress(post_title, summary)
