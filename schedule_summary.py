from datetime import datetime, timedelta
import calendar
import argparse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os.path

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_service():
    """Retrieves a Google Calendar API service instance.

    The authentication flow follows these steps:
    1. Uses existing token if available
    2. Attempts to refresh token if expired
    3. Performs OAuth2 authentication via local server if new auth is needed

    Returns:
        googleapiclient.discovery.Resource: Google Calendar API service instance

    Raises:
        google.auth.exceptions.RefreshError: If token refresh fails
        google.auth.exceptions.DefaultCredentialsError: If unable to obtain credentials
    """
    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def list_calendars():
    """利用可能なカレンダーの一覧を表示"""
    service = get_calendar_service()
    calendars_result = service.calendarList().list().execute()
    calendars = calendars_result.get('items', [])

    if not calendars:
        print('利用可能なカレンダーが見つかりませんでした。')
    else:
        print('\n利用可能なカレンダー:')
        for calendar in calendars:
            print(f"カレンダー名: {calendar['summary']}")
            print(f"カレンダーID: {calendar['id']}")
            print('-' * 50)

def get_month_range(target_month):
    """指定された月の開始日と終了日を取得"""
    today = datetime.today()
    
    if target_month == "current":
        year = today.year
        month = today.month
    else:  # next month
        if today.month == 12:
            year = today.year + 1
            month = 1
        else:
            year = today.year
            month = today.month + 1
    
    _, last_day = calendar.monthrange(year, month)
    
    start_date = datetime(year, month, 1, 0, 0, 0).isoformat() + 'Z'
    end_date = datetime(year, month, last_day, 23, 59, 59).isoformat() + 'Z'
    
    return start_date, end_date

def calculate_duration(event):
    """イベントの所要時間を計算（分単位）"""
    start = event['start'].get('dateTime')
    end = event['end'].get('dateTime')
    
    if not start or not end:  # 終日イベントの場合はスキップ
        return 0
        
    start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
    end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))
    
    duration = end_time - start_time
    return duration.total_seconds() / 60

def analyze_events(calendar_id, title, target_month):
    """指定されたカレンダーの特定タイトルのイベントを集計"""
    service = get_calendar_service()
    start_date, end_date = get_month_range(target_month)
    
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start_date,
        timeMax=end_date,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    total_duration = 0
    matching_events = []
    
    for event in events:
        if title.lower() in event.get('summary', '').lower():
            duration = calculate_duration(event)
            if duration > 0:
                total_duration += duration
                matching_events.append({
                    'summary': event['summary'],
                    'start': event['start']['dateTime'],
                    'duration': duration
                })
    
    return total_duration, matching_events

def main():
    parser = argparse.ArgumentParser(description='Google Calendar Event Duration Analyzer')
    parser.add_argument('--list-calendars', action='store_true',
                      help='利用可能なカレンダーの一覧を表示')
    parser.add_argument('--calendar-id', 
                      help='対象とするカレンダーID')
    parser.add_argument('--title', 
                      help='検索するイベントのタイトル')
    parser.add_argument('--month', choices=['current', 'next'], default='current',
                      help='対象月（current: 今月, next: 来月）')
    
    args = parser.parse_args()
    
    try:
        if args.list_calendars:
            list_calendars()
            return

        if not args.calendar_id or not args.title:
            print("カレンダーIDとタイトルは必須です。")
            print("利用可能なカレンダーを確認するには --list-calendars オプションを使用してください。")
            return

        total_duration, matching_events = analyze_events(args.calendar_id, args.title, args.month)
        
        print(f"\n検索タイトル: {args.title}")
        print(f"対象カレンダー: {args.calendar_id}")
        print(f"対象月: {'今月' if args.month == 'current' else '来月'}")
        print(f"\n合計時間: {total_duration/60:.1f}時間 ({total_duration:.0f}分)")
        
        if matching_events:
            print("\n該当イベント一覧:")
            for event in matching_events:
                start_time = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                print(f"- {start_time.strftime('%Y-%m-%d %H:%M')} : {event['summary']} "
                      f"({event['duration']:.0f}分)")
        else:
            print("\n該当するイベントは見つかりませんでした。")
            
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == '__main__':
    main()