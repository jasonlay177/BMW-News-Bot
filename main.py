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


def get_economic_news():
  print("📈 오늘의 주요 경제 뉴스를 수집하는 중...")
  # 구글 뉴스 RSS에서 경제 관련 최신 뉴스 검색
  rss_url = (
      "https://news.google.com/rss/search?q=%EA%B2%BD%EC%A0%9C&hl=ko&gl=KR&ceid=KR:ko"
  )
  feed = feedparser.parse(rss_url)

  news_list = []
  # 상위 5개의 뉴스를 수집하도록 넉넉히 가져옵니다
  for entry in feed.entries[:5]:
    news_list.append(f"제목: {entry.title}\n링크: {entry.link}\n")

  return "\n".join(news_list)


def summarize_news(news_text):
  print(
      "🤖 Gemini AI가 미국 증시 마감 분석 및 국내 주요 경제 뉴스 임팩트 순"
      " 선별 중..."
  )
  prompt = f"""
    당신은 전문 수석 애널리스트입니다. 아래의 원본 뉴스와 전일 글로벌 시장의 흐름을 바탕으로, 
    오늘 국내 투자자들이 가장 먼저 확인해야 할 '프리미엄 모닝 브리핑' 웹 블로그 포스트를 작성해 주세요.
    
    반드시 아래의 구조와 규칙을 지켜서 순수 HTML 태그 문자열만 반환해 주세요. (Markdown 백틱 ```html ... ``` 절대 사용 금지)

    [포스팅 구성 및 작성 규칙]
    
    1. 도입부: 당일 마감한 미국 주식시장(뉴욕증시) 상황 요약
       - <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
         <h3>🇺🇸 당일 미국 증시 마감 체크포인트</h3>
         - 다우, S&P 500, 나스닥 등 주요 지수의 마감 흐름과 분위기를 가볍고 친근한 어조(~해요)로 요약해 주세요.
         - 시장을 흔들었던 핵심 특이사항이나 이슈 2~3가지를 <ul>과 <li> 태그를 사용해 깔끔하게 짚어주세요.
         - 나스닥 상위 100 종목중 상승률이 높았던 5가지 종목을 골라 상승률과 상승이유를 설명해주세요. 그리고 해당 종목과 관련이 있을 거같은 국내 종목을 언급해주세요.
         </div>

    2. 전환부: 국내 뉴스 섹션 시작 알림 (이 박스를 반드시 추가해 주세요)
       - <div style="background-color: #ffffff; padding: 15px 20px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
         <h3 style="margin-top: 0; margin-bottom: 0; color: #1a202c;">🇰🇷 주요 국내 경제 뉴스</h3>
         </div>
         
    3. 본문: 주식 시장에 미치는 파급 효과가 **가장 큰 순서(임팩트 1위부터 5위)**로 엄선한 국내외 주요 경제 뉴스
       - 총 5가지 뉴스를 순서대로 나열해 주세요.
       - 각 뉴스 제목은 <h3> 태그를 사용하고 앞에 📈 순위(예: 1위, 2위...)를 붙여주세요. (예: <h3>📈 1위: 타이틀내용</h3>)
       - 본문 내용은 <ul>과 <li> 태그를 사용하여 핵심 요약 2~3가지로 정리해 주세요.
       - 중요한 경제 키워드나 수치는 <strong> 태그로 강조해 주세요.
       - **기업명 표기**: 각 뉴스 항목의 마지막에 해당 뉴스와 직접적인 관련이 있는 핵심 기업명(또는 종목명)을 **(관련 기업: 종목명)** 형태로 반드시 기재해 주세요.

    4. 마무리: 오늘 장을 시작하는 투자자들을 위한 한 줄 인사이트 및 코멘트
       - <p><i>💡 애널리스트 한 줄 코멘트: ...</i></p> 형식으로 덧붙여 주세요.

    [뉴스 원본 참고 자료]
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
  news_data = get_economic_news()  # 함수 이름 변경 반영
  if not news_data:
    print("수집된 뉴스가 없습니다.")
  else:
    summary = summarize_news(news_data)
    print("\n" + "=" * 40)
    print("✨ [오늘의 경제 뉴스 요약 결과]")
    print("=" * 40)
    print(summary)

    # 포스팅 제목 생성 (오늘 날짜 포함)
    today_date = datetime.now().strftime("%Y년 %m월 %d일")
    post_title = f"📈 오늘의 경제 트렌드 브리핑 ({today_date})"

    # 워드프레스 포스팅 실행
    post_to_wordpress(post_title, summary)
