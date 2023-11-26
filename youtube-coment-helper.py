import os
import csv
import time
from pathlib import Path
import io
import MyOpenAIClient
import MyYoutube
import ScrapBox

STREMER_NAME = "YOUR Youtube NAME"
SCRAPBOX_PROJECT = "IF you have scrapbox-project"

def get_scrapbox_titles(text, info_titles):
    for title in info_titles:
        if title in text:
            return title
    return None

# Main function
def main():
    openai_client = MyOpenAIClient.MyOpenAIClient()
    youtube_client = MyYoutube.MyYouTubeClient()
    #scrapbox_client = ScrapBox.ScrapboxAPI(SCRAPBOX_PROJECT)

    #info_titles = scrapbox_client.get_page_titles()
    #info_titles.remove(STREMER_NAME)

    video_id = input("Video ID >> ")
    live_chat_id = youtube_client.get_live_chat_id(video_id)

    if not live_chat_id:
        return

    comment_voice_index = 0
    while True:
        try:
            live_comments = youtube_client.get_live_chat_messages(live_chat_id)
            
            for comment in live_comments:
                # 初コメントの人に挨拶
                if comment[0] != STREMER_NAME:
                    if youtube_client.update_listner(comment[0]) :
                        openai_client.text_to_speech_and_play(
                            text=comment[0] + 'さん、いらっしゃいませおはようございます！',
                            voice_index=300000
                        )
                
                    # コメント内容を読み上げる
                    openai_client.text_to_speech_and_play(
                        text=comment[0] + 'さん' + comment[1],
                        voice_index=comment_voice_index
                    )
                    comment_voice_index += 1

                # GPTで始まっていたらGPTで回答を生成してコメント投稿
                if comment[1].startswith("GPT"):
                    # Scrapboxの情報が含まれていたらScrapboxを参照
                    #if get_info_titles(text=comment[1], info_titles=info_titles) != None:
                    #    reply = openai_client.generate_reply_with_gpt4_preview(
                    #        message = comment[1].replace('GPT', ''),
                    #        model="gpt-4-1106-preview"
                    #    )
                    #else:
                    reply = openai_client.generate_reply_with_gpt(
                        message = comment[1].replace('GPT', ''),
                        model="gpt-3.5-turbo"
                    )
                    youtube_client.post_to_live_chat(
                        live_chat_id=live_chat_id,
                        message = reply
                    )

            # Youtubeのコメント取得リクエスト制限回避のためにSleep
            time.sleep(10)
        except Exception as e:
            print(f"Error during main loop: {e}")
            break

if __name__ == "__main__":
    main()
