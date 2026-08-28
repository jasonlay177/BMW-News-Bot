import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import feedparser
import google.generativeai as genai

# 1. API 키 및 이메일 정보 설정 (GitHub Secret에서 안전하게 가져옵니다)
api_key = os.environ.get("GEMINI_API_KEY")
sender_email = os.environ.get("MY_EMAIL")
email_password = os.environ.get("EMAIL_PASSWORD")
receiver_email = os.environ.get("RECEIVER_EMAIL")

if not api_key:
    raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다!")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3.6-flash')

def get_bmw_news():
    print(" BMW 최신 뉴스를 수집하는 중...")
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
    특수문자는 사용하지 말고 글자 사이즈 12로 깔끔하게 번호만 붙여서. 각 뉴스당 5~6줄 정도 분량으로.

    [뉴스 원본]
    {news_text}
    """
    response = model.generate_content(prompt)
    return response.text

def send_email(summary_text):
    print("📧 이메일 발송 중...")
    # 메일 제목과 본문 설정
    msg = MIMEMultipart()
    msg['Subject'] = ' 오늘 아침 BMW 뉴스 요약'
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    # 이메일 본문 내용 추가
    content = f"안녕하세요! 오늘 아침 BMW 뉴스 요약 봇입니다.\n\n{summary_text}"
    msg.attach(MIMEText(content, 'plain', 'utf-8'))
    
    # Gmail SMTP 서버를 통해 메일 전송
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() # 보안 연결
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
        
        # 이메일 보내기 실행
        send_email(summary)
