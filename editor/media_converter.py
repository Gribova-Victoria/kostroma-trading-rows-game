from moviepy.editor import *
import cv2
from PIL import Image, ImageSequence
import shutil
import os
import speech_recognition as sr  # pip install SpeechRecognition
import subprocess

class MediaConverter:
    def __init__(self):
        pass

    def loadVideo(self, fname):
        ''' Ищет видео по указанному пути или с указанной камеры.'''
        video = cv2.VideoCapture(fname)
        counter = 300
        while counter > 0 and not video.isOpened():  # для файлов должно сработать сразу
            cv2.waitKey(10)
            counter -= 1
        if counter == 0:
            raise IOError('Failed to open video.')
        return video

    def changeVideoResolution(self, path, resolution): 
        # путь к файлу, кортеж - разрешение (напр. (480, 480)), новое имя (с расширением файла)
        vid = self.loadVideo(path)
        height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        if height==width and height<=640 :
            return
        extension = self.getFileExtension(path)
        supportFileName = self.getFilePathWithoutFname(path)+"supportFile"+extension
        shutil.copy(path, supportFileName)
        video = VideoFileClip(path)
        result = video.resize(resolution)
        result.write_videofile(supportFileName)
        vid.release()
        os.remove(path)
        shutil.copy(supportFileName, path)
        os.remove(supportFileName)

    def changeImageResolution(self, path, resolution): 
        # путь к файлу, кортеж - разрешение (напр. (480, 480)), новое имя (с расширением файла)
        extension = self.getFileExtension(path)
        supportFileName = self.getFilePathWithoutFname(path)+"supportFile"+extension
        shutil.copy(path, supportFileName)
        image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        result = cv2.resize(image, resolution)
        cv2.imwrite(supportFileName, result)
        os.remove(path)
        shutil.copy(supportFileName, path)
        os.remove(supportFileName)

    def changeGIFResolution(self, path, resolution):  
        extension = self.getFileExtension(path)
        supportFileName = self.getFilePathWithoutFname(path)+"supportFile"+extension
        shutil.copy(path, supportFileName)
        gif = Image.open(path)
        frames = ImageSequence.Iterator(gif)
        frames = self.thumbnails(frames, resolution)
        om = next(frames) # Handle first frame separately
        om.info = gif.info # Copy sequence info
        om.save(supportFileName, save_all=True, append_images=list(frames), loop=0)
        os.remove(path)
        shutil.copy(supportFileName, path)
        os.remove(supportFileName)


    def thumbnails(self, frames, resolution): # вспомогательная функция
        # Output (max) size
        #size = 320, 240
        #size = resolution
        for frame in frames:
            thumbnail = frame.copy()
            #thumbnail.thumbnail(size, Image.ANTIALIAS)
            thumbnail = thumbnail.resize(resolution)
            yield thumbnail

    def getFileExtension(self, path):
        lastDotIndex = path.rindex(".")
        return path[lastDotIndex:]

    def getFilePathWithoutFname(self, path):
        try:
            lastIndexOfSlash = path.rindex("/")
        except:
            lastIndexOfSlash = 0
        return path[:lastIndexOfSlash]

    FFMPEG_PATH = r'ffmpeg\bin\ffmpeg.exe'
    AUDIO_WAV = 'audio.wav'
    def voiceToText(self, audio_ogg):
        process = subprocess.run([self.FFMPEG_PATH, '-loglevel', 'quiet', '-i', audio_ogg,
                                  '-y', '-c:a', 'pcm_s16le', self.AUDIO_WAV])
        r = sr.Recognizer()
        with sr.AudioFile(self.AUDIO_WAV) as source:
            audio = r.record(source)
        try:
            text = r.recognize_google(audio, language = 'ru-RU')
        except:
            text = "#"
        os.remove(self.AUDIO_WAV)
        os.remove(audio_ogg)
        print(text)  # TODO: отправлять сообщением ботом
        return text

    OGG = '.ogg'
    def convertToOgg(self, path):
        """Конвертирует файл в формат .ogg и возвращает путь до нового файла."""
        if self.getFileExtension(path) != OGG:
            new_filepath = os.path.splitext(path)[0] + self.OGG
            process = subprocess.run([self.FFMPEG_PATH, '-i', path, '-acodec',
                                      'libmp3lame', new_filepath])
            path = new_filepath
        return path
