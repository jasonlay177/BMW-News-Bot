import base64
from datetime import datetime
import os
import feedparser
import google.generativeai as genai
import requests  # 워드프레스 REST API 통신용 라이브러리

# 1. API 키 및 설정 (GitHub Secret에서 안전하게 가져옵니다)
api_key = os.environ.get("GEMINI_API_KEY")

# 이메일 관련 변수 (현재는 주석 처리됨)
# sender_email = os.environ.get("MY_EMAIL")
# email_password = os.environ.get("EMAIL_PASSWORD")
# receiver_email = os.environ.get("RECEIVER_EMAIL")

# 워드프레스 연동 정보 설정 (요청하신 변수명 적용)
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")

if not api_key:
  raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다!")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-3.5-flash")  # 안정적인 모델 버전


def get_bmw_news():
  print("🚗 BMW 최신 뉴스를 수집하는 중...")
  # 검색어를 조금 더 확실하게 잡힐 수 있도록 인코딩 파라미터 포함
  rss_url = "https://news.google.com/rss/search?q=BMW&hl=ko&gl=KR&ceid=KR:ko"
  feed = feedparser.parse(rss_url)

  print(f"🔍 디버깅: 수집된 전체 피드 개수: {len(feed.entries)}")

  news_list = []
  # 안전하게 최대 3개 혹은 전체 피드 개수만큼 가져오기
  for entry in feed.entries[:3]:
    news_list.append(f"제목: {entry.title}\n링크: {entry.link}\n")

  if not news_list:
    # 만약 위 URL에서 안 긁어와지면 대체 검색어로 한 번 더 시도할 수 있습니다.
    print("⚠️ 기본 RSS에서 뉴스를 찾지 못해 대체 검색어로 재시도합니다.")
    alt_url = (
        "https://news.google.com/rss/search?q=%EB%B9%84%EC%97%84%EB%8D%94%EB%B9%"
        "84%EC%9C%A0&hl=ko&gl=KR&ceid=KR:ko"
    )  # '비엠더블유' 인코딩 검색
    feed = feedparser.parse(alt_url)
    for entry in feed.entries[:3]:
      news_list.append(f"제목: {entry.title}\n링크: {entry.link}\n")

  return "\n".join(news_list)


def summarize_news(news_text):
  print("🤖 Gemini AI가 친근한 블로그 스타일로 뉴스를 요약하는 중...")
  prompt = f"""
    다음은 최근 BMW 관련 뉴스 목록입니다. 
    이 내용들을 바탕으로 일반 독자들이 쉽고 흥미롭게 읽을 수 있는 트렌디한 자동차 블로그 글 형식으로 요약해 주세요.
    
    - 어조: 딱딱한 비즈니스 톤 대신, 자동차를 좋아하는 친구에게 수다 떨듯 친근하고 부드러운 어조(~해요, ~랍니다 등)로 작성해 주세요.
    - 각 뉴스 제목은 <h3> 태그를 사용하고 앞에 아이콘을 붙여서 호기심을 유발해 주세요.
    - 본문 내용은 <ul>과 <li> 태g를 사용하여 핵심 내용 위주로 2~3개의 깔끔한 포인트로 정리해 주세요.
    - 중요한 키워드나 재밌는 숫자는 <strong> 태그로 콕 집어 강조해 주세요.
    - 전체 내용 끝에 독자들에게 가볍게 건네는 한 줄 코멘트나 소감을 <p><i>...</i></p> 태그로 덧붙여 주세요.
    - 주의: Markdown 백틱(```html ... ```) 같은 마크다운 기호는 절대 쓰지 말고, 순수 HTML 태그 문자열만 반환해 주세요.

    [뉴스 원본]
    {news_text}
    """
  response = model.generate_content(prompt)
  return response.text


# [주석 처리] 기존 GitHub Pages용 HTML 파일 생성 함수
# def save_to_html(summary_text):
#     ...


# [주석 처리] 기존 이메일 발송 함수
# def send_email(summary_text):
#     ...


# 워드프레스 자동 포스팅 함수
def post_to_wordpress(title, summary_text):
  print("📝 스타일이 적용된 포스팅을 워드프레스에 전송하는 중...")

  if not WP_URL or not WP_USER or not WP_APP_PASSWORD:
    print("⚠️ 워드프레스 설정(Secret)이 누락되어 포스팅을 건너뜁니다.")
    return

  api_url = f"{WP_URL}/wp-json/wp/v2/posts"

  # Basic Auth 인증 헤더 생성
  credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
  token = base64.b64encode(credentials.encode()).decode()
  headers = {
      "Authorization": f"Basic {token}",
      "Content-Type": "application/json",
  }

  # Gemini가 이미 HTML 태그를 포함해서 주므로 replace 없이 그대로 사용합니다!
  data = {
      "title": title,
      "content": summary_text,
      "status": "publish",
      # "categories": [1] # 필요하다면 워드프레스의 카테고리 ID 번호를 넣을 수 있습니다.
  }

  try:
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 201:
      print("✨ 멋지게 꾸며진 워드프레스 포스팅 완료!")
    else:
      print(f"❌ 포스팅 실패: {response.status_code}, {response.text}")
  except Exception as e:
    print(f"❌ 통신 중 오류 발생: {e}")

  api_url = f"{WP_URL}/wp-json/wp/v2/posts"

  # Basic Auth 인증 헤더 생성
  credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
  token = base64.b64encode(credentials.encode()).decode()
  headers = {
      "Authorization": f"Basic {token}",
      "Content-Type": "application/json",
  }

  # 본문 줄바꿈을 HTML 태그(<br>)로 변환
  formatted_content = summary_text.replace("\n", "<br>")

  # 전송할 데이터 구조 (status: 'publish'는 즉시 발행, 'draft'는 임시글 저장)
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
