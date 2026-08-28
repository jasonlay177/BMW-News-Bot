import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import feedparser
import google.generativeai as genai
from datetime import datetime

# 1. API 키 및 이메일 정보 설정 (GitHub Secret에서 안전하게 가져옵니다)
api_key = os.environ.get("GEMINI_API_KEY")
sender_email = os.environ.get("MY_EMAIL")
email_password = os.environ.get("EMAIL_PASSWORD")
receiver_email = os.environ.get("RECEIVER_EMAIL")

if not api_key:
    raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다!")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash') # 모델명을 안정적인 버전으로 수정했습니다

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
    이 내용들을 바탕으로 주요 뉴스 5가지를 요약해서 경영진에 보고하는 형식으로 만들어주세요.
    특수문자는 사용하지 말고 깔끔하게 번호만 붙여서. 각 뉴스당 5~6줄 정도 분량으로.

    [뉴스 원본]
    {news_text}
    """
    response = model.generate_content(prompt)
    return response.text

def save_to_html(summary_text):
    print("🌐 블로그 HTML 파일 생성 중...")
    today_date = datetime.now().strftime("%Y년 %m월 %d일")
    
    # 줄바꿈(엔터)을 HTML 줄바꿈(<br>)으로 변환
    formatted_summary = summary_text.replace('\n', '<br>')
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <title>BMW News Bot - {today_date}</title>
    <style>
        body {{ font-family: 'Apple SD Gothic Neo', sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; color: #333; }}
        h1 {{ color: #111; border-bottom: 2px solid #000; padding-bottom: 10px; }}
        .date {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
        .content {{ background: #f9f9f9; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    </style>
</head>
<body>
    <h1>🚗 BMW Daily News Bot</h1>
    <div class="date">발행일: {today_date}</div>
    <div class="content">
        <p>{formatted_summary}</p>
    </div>
</body>
</html>
"""
    # index.html 파일로 저장 (접속했을 때 바로 이 내용이 보임)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ index.html 파일 생성 완료!")

def send_email(summary_text):
    print("📧 이메일 발송 중...")
    if not sender_email or not email_password or not receiver_email:
        print("⚠️ 이메일 설정(Secret)이 누락되어 이메일 발송을 건너뜁니다.")
        return

    msg = MIMEMultipart()
    msg['Subject'] = '오늘 아침 BMW 뉴스 요약'
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    content = f"안녕하세요! 오늘 아침 BMW 뉴스 요약 봇입니다.\n\n{summary_text}"
    msg.attach(MIMEText(content, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, email_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("✅ 메일 발송 성공!")
    except Exception as e:
        print(f"❌ 메일 발송 실패: {e}")

if __name__ == "__main__":
    news_data = get_bmw_news()
    if not news_data:
        print("수집된 뉴스가 없습니다.")
    else:
        summary = summarize_news(news_data)
        print("\n" + "="*40)
        print("✨ [BMW 뉴스 요약 결과]")
        print("="*40)
        print(summary)
        
        # 1. 블로그 파일(index.html)로 저장
        save_to_html(summary)
        
        # 2. 이메일 보내기 실행
        send_email(summary)
