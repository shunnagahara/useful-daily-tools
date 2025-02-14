import os
from google.cloud import speech_v1
from google.cloud import storage
import ffmpeg
from pydub import AudioSegment
from datetime import datetime
import argparse

def extract_audio_from_video(video_path, audio_path):
    """動画から音声を抽出してWAVファイルとして保存"""
    try:
        stream = ffmpeg.input(video_path)
        stream = ffmpeg.output(stream, audio_path, acodec='pcm_s16le', ac=1, ar='16k')
        ffmpeg.run(stream, overwrite_output=True)
    except ffmpeg.Error as e:
        print(f"エラーが発生しました: {e.stderr.decode()}")
        raise

def convert_to_mono_wav(input_audio_path, output_audio_path):
    """音声をモノラル、16kHzのWAVに変換"""
    try:
        stream = ffmpeg.input(input_audio_path)
        stream = ffmpeg.output(stream, output_audio_path, acodec='pcm_s16le', ac=1, ar='16k')
        ffmpeg.run(stream, overwrite_output=True)
    except ffmpeg.Error as e:
        print(f"エラーが発生しました: {e.stderr.decode()}")
        raise

def upload_to_gcs(bucket_name, source_file_path, destination_blob_name):
    """ファイルをGoogle Cloud Storageにアップロード"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_path)
    return f"gs://{bucket_name}/{destination_blob_name}"

def transcribe_audio(gcs_uri):
    """Speech-to-Text APIを使用して音声を文字起こし"""
    client = speech_v1.SpeechClient()

    audio = speech_v1.RecognitionAudio(uri=gcs_uri)
    config = speech_v1.RecognitionConfig(
        encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ja-JP",
        alternative_language_codes=["en-US"],  # 英語を追加
        enable_automatic_punctuation=True,
    )

    operation = client.long_running_recognize(config=config, audio=audio)
    print("文字起こしを開始しました...")
    response = operation.result()

    # 現在の日時をファイル名に追加
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"transcription_{timestamp}.txt"

    # 文字起こし結果をテキストファイルに保存
    with open(output_filename, "w", encoding="utf-8") as f:
        for result in response.results:
            f.write(result.alternatives[0].transcript + "\n")

    return output_filename  # ファイル名を返す

def main():
    # ArgumentParserの設定
    parser = argparse.ArgumentParser(description='動画から音声を抽出し、文字起こしを行います。')
    parser.add_argument('--credentials', required=True,
                      help='Google Cloud の認証情報JSONファイルへのパス')
    parser.add_argument('--video', required=True,
                      help='文字起こしを行う動画ファイルへのパス')
    args = parser.parse_args()
    
    # 環境変数の設定
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = args.credentials
    
    # パラメータ設定
    video_path = args.video
    temp_audio_path = "temp_audio.wav"
    final_audio_path = "final_audio.wav"
    bucket_name = "speech-to-text-useful-daily-tools"
    destination_blob_name = "audio_for_transcription.wav"

    # 処理実行
    print("音声を抽出中...")
    extract_audio_from_video(video_path, temp_audio_path)
    
    print("音声を変換中...")
    convert_to_mono_wav(temp_audio_path, final_audio_path)
    
    print("Google Cloud Storageにアップロード中...")
    gcs_uri = upload_to_gcs(bucket_name, final_audio_path, destination_blob_name)
    
    print("文字起こしを実行中...")
    output_file = transcribe_audio(gcs_uri)
    
    # 一時ファイルの削除
    os.remove(temp_audio_path)
    os.remove(final_audio_path)
    
    print(f"文字起こしが完了しました。結果は {output_file} に保存されています。")

if __name__ == "__main__":
    main()