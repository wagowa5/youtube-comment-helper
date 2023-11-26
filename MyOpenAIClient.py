from openai import OpenAI
import os
from pathlib import Path
import io
import pygame
from pydub import AudioSegment
from pydub.playback import play
import requests
import json

SYSTEM_MESSAGE = "I am designed to assist users with information related to the 'Specified Information(ScrapBox-project)'."

# ここかScrapBoxAPIClientを直す
def get_scrapbox_info(title):
    response = requests.get(f"https://scrapbox.io/api/pages/:projectname/{title}")
    if response.status_code == 200:
        data_content = response.json()
        texts = [line['text'] for line in data_content['lines']]

        information = str('\n'.join(texts))
    else:
        information = ""
    
    return information

class MyOpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    def text_to_speech(self, text, voice_index, model="tts-1", voice="nova", speed=1.0):
        try:
            audio_directory = Path.cwd() / "audio"
            audio_directory.mkdir(parents=True, exist_ok=True)
            speech_file_path = audio_directory / f"audio_{voice}_{model}_{voice_index}.mp3"

            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed
            )

            if speech_file_path.exists():
                speech_file_path.unlink()

            response.stream_to_file(speech_file_path)
            return speech_file_path
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def play_audio(self, file_path, speed=1.0):
        sound = AudioSegment.from_file(file_path)
        sound_with_altered_speed = sound._spawn(sound.raw_data, overrides={
            "frame_rate": int(sound.frame_rate * speed)
        }).set_frame_rate(sound.frame_rate)

        byte_io = io.BytesIO()
        sound_with_altered_speed.export(byte_io, format="wav")
        byte_io.seek(0)

        pygame.mixer.init()
        pygame.mixer.music.load(byte_io)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(500)

    def text_to_speech_and_play(self, text, voice_index):
        try:
            self.play_audio(self.text_to_speech(text=text, voice_index=voice_index))
        except Exception as e:
            print(f"Error in text to speech: {e}")

    def generate_reply_with_gpt(self, message, model="gpt-3.5-turbo-0613", temperature=0.8):
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    #{"role": "assistant", "content": GPT_ASSISTANT},
                    {"role": "user", "content": message}
                ],
                max_tokens=200,
                temperature=0.8
            )
            print(response.choices[0].message.content)
            reply = response.choices[0].message.content
            return reply
        except Exception as e:
            print(f"Error generating reply with GPT: {e}")
            return None
    
    def generate_reply_with_gpt4_preview(self, message, model="gpt-4-1106-preview", temperature=0.8):
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-0613",
                messages=[
                    #{"role": "system", "content": "挨拶を返してください！"},
                    {"role": "system", "content": SYSTEM_MESSAGE},
                    {"role": "user", "content": message}
                ],
                max_tokens=990,
                temperature=0.8,
                functions=[
                    {
                        "name": "get_scrapbox_info",
                        "description": "Scrapboxプロジェクトの情報を取得する",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "ページのタイトル",
                                }
                            },
                            "required": ["title"],
                        },
                    }
                ],
                function_call="auto",
            )
            
            reply = response.choices[0].message
            if reply.function_call != None:
                function_name = reply.function_call.name

                arguments_dict = json.loads(reply.function_call.arguments)
                title = arguments_dict["title"]
                function_response = get_scrapbox_info(title)

                # 関数結果と過去のチャット履歴を送る
                reply2 = self.client.chat.completions.create(
                    model="gpt-3.5-turbo-0613",
                    messages=[
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "function_call"},
                        {
                            "role": "function",
                            "name": str(function_name),
                            "content": str(function_response)
                        },
                    ],
                )
                return reply2.choices[0].message.content
            
            print(reply)
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating reply with GPT: {e}")
            return None
