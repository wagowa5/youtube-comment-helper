from operator import truediv
import os
from re import T
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from pathlib import Path
import time


class MyYouTubeClient:
    def __init__(self):
        # Google APIクライアントを作成します
        self.client = googleapiclient.discovery.build("youtube", "v3", developerKey=os.environ['GOOGLE_API_KEY'])

        # 認証フローを実行し、認証情報を取得します
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            "google credetialのjsonファイルパス",
            ["https://www.googleapis.com/auth/youtube.force-ssl"]
        )
        credentials = flow.run_local_server(port=0)

        # 認証情報を使ってYouTube APIクライアントを作成します
        self.youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

        # 変数の初期化
        self.next_page_token = None # Youtubeのliveチャットコメントに使用
        self.comment_history = [] # ライブチャット履歴を格納
        self.listner_history = [] # 視聴者リスト
        

    def get_live_chat_id(self, video_id):
        request = self.youtube.videos().list(
            part="liveStreamingDetails",
            id=video_id
        )
        response = request.execute()

        print(response)

        if "items" in response and len(response["items"]) > 0:
            return response["items"][0]["liveStreamingDetails"]["activeLiveChatId"]
        else:
            raise Exception("ライブチャットが見つかりませんでした")

    def get_live_chat_messages(self, live_chat_id):
        request = self.youtube.liveChatMessages().list(
            liveChatId=live_chat_id,
            part="snippet,authorDetails",
            maxResults=2000,
            pageToken=self.next_page_token
        )
        response = request.execute()

        response_comments = response["items"]
        comments = []
        for comment in response_comments:
            user_name = comment["authorDetails"]["displayName"]
            comment_text = comment["snippet"]["displayMessage"]
            new_comment = [user_name, comment_text]
            comments.append(new_comment)
        
        self.next_page_token = response["nextPageToken"]
        return comments

    def post_to_live_chat(self, live_chat_id, message):
        # messageを199文字ごとに分割
        chunks = self.split_text(message, 199)

        try:
            for chunk in chunks:
                self.youtube.liveChatMessages().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "liveChatId": live_chat_id,
                            "type": "textMessageEvent",
                            "textMessageDetails": {
                                "messageText": chunk
                            }
                        }
                    }
                ).execute()
                # 連投制限回避のため5秒待機
                time.sleep(5)

        except Exception as e:
            print("投稿中にエラーが発生しました:", e)
    
    def update_listner(self, user_name):
        if (user_name not in self.listner_history) :
            self.listner_history.append(user_name)
            return True
        else:
            return False
        
    # 199文字ごとに分割する関数
    def split_text(self, text, chunk_size):
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
