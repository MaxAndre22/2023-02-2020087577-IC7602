import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import Menu
import os
import pyaudio
import wave
import numpy as np
import threading
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
from zipfile import ZipFile
from scipy.io.wavfile import write
from os import remove
import time
from scipy.fft import rfft
from PIL import Image, ImageTk
import sounddevice as sd
import struct
import matplotlib.pyplot as plt

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 1
WAVE_OUTPUT_FILENAME = "output.wav"
PLAY_RANGE = 5

frames = []
recording = False
wavFile = []
fourier_frames = []
vec_fourier_frames = []
external_wav_path = ""


def to_atm(chunksList, wavFilePath):
    file = open("chunks", "wb")
    content = array_to_bytes(chunksList)
    file.write(content)
    file.close
    global frames
    with ZipFile('file.atm', 'w') as zip:
        zip.write('chunks')
        zip.write(wavFilePath)
        print(chunksList)
    try:
        os.remove("chunks")
    except:
        print("File already deleted")


def from_atm(filepath):
    with ZipFile(filepath) as zip:
        files = zip.namelist()
        for i in range(0, len(files)):
            if (".wav" in files[i]):
                global wavFile
                zip.extract(files[i])
                wavFile = open_wav_file(files[i])
            elif (files[i] == "chunks"):
                global frames
                frames = bytes_to_array(zip.read(files[i]))

                print(type(frames))
                print(frames)


def array_to_bytes(x):
    np_bytes = BytesIO()
    np.save(np_bytes, x, allow_pickle=True)
    return np_bytes.getvalue()


def bytes_to_array(b):
    np_bytes = BytesIO(b)
    return np.load(np_bytes, allow_pickle=True)


def open_wav_file(file):
    return wave.open(file, 'rb')


class Autrumn(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Autrumn")

        # create a menubar
        menubar = Menu(self)
        self.config(menu=menubar)

        # create a menu
        autrumn_menu = Menu(menubar, tearoff=False)

        autrumn_menu.add_command(label='Analizador', command=lambda: self.show_frame(Analizador))
        autrumn_menu.add_command(label='Reproductor', command=lambda: self.show_frame(Reproductor))
        autrumn_menu.add_separator()
        autrumn_menu.add_command(
            label='Exit',
            command=self.destroy
        )

        menubar.add_cascade(
            label="Menú",
            menu=autrumn_menu
        )

        self.geometry("700x1200")

        container = tk.Frame(self)
        container = tk.Frame(self)
        container.grid(row=1, column=1, padx=10, pady=10)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (Analizador, Reproductor):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(Analizador)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class Analizador(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        top_frame = tk.Frame(self, width=200, height=400, bg='grey')
        label = ttk.Label(top_frame, text="Analizador", font="Consolas")
        top_frame.grid(row=0, column=0, padx=10, pady=5)
        label.grid(row=0, column=0, padx=10, pady=10)

        self.fig = Figure(figsize=(5, 1), dpi=100)
        self.fig.add_subplot(111).plot(frames)
        self.fig2 = Figure(figsize=(5, 3), dpi=100)
        self.fig2.add_subplot(111).hist(fourier_frames, bins=100)
        self.ax = 0
        self.entry = ttk.Entry(top_frame)
        self.entry.grid(row=0, column=1, padx=10, pady=10)

        self.btn_load = ttk.Button(top_frame, text="Load",
                                   command=self.start_loading_thread)
        self.btn_load.grid(row=1, column=1, padx=10, pady=10)

        start_recording_button = ttk.Button(
            top_frame,
            text='Start recording',
            compound=tk.LEFT,
            command=self.start_recording_thread
        )
        start_recording_button.grid(row=0, column=2, padx=10, pady=10)

        stop_recording_button = ttk.Button(
            top_frame,
            text='Stop recording',
            compound=tk.LEFT,
            command=self.recordingAudio
        )
        stop_recording_button.grid(row=0, column=3, padx=10, pady=10)

        open_audio_button = ttk.Button(
            top_frame,
            text='Open audio',
            compound=tk.LEFT,
            command=self.recordingAudio
        )
        open_audio_button.grid(row=0, column=4, padx=10, pady=10)

        self.frame1 = tk.Frame(self)
        self.frame2 = tk.Frame(self)

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame1)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, self)
        self.toolbar2 = NavigationToolbar2Tk(self.canvas2, self.frame2)

        self.frame1.grid(row=4, column=0, padx=10, pady=10)
        self.canvas.get_tk_widget().grid(row=5, column=0, padx=10, pady=10)
        self.frame2.grid(row=6, column=0, padx=10, pady=10)
        self.canvas2.get_tk_widget().grid(row=7, column=0, padx=10, pady=10)

    def start_loading_thread(self):
        threading.Thread(target=self.load_data).start()

    def load_data(self):
        file = self.entry.get()
        print(file)
        global frames
        frames = []
        if(file != ""):
            global frames
            global external_wav_path
            external_wav_path = file
            print(external_wav_path)
            wavFile = wave.open(external_wav_path, 'rb')
            frames = []
            while(True):
                data = wavFile.readframes(CHUNK)
                if(len(data) > 0):
                    frames.append(data)
                else:
                    break
            wavFile.close()

    def start_recording_thread(self):
        threading.Thread(target=self.recordingAudio).start()

    def recordingAudio(self):
        global recording
        recording = True
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True, frames_per_buffer=CHUNK)
        print("Recording...")
        while(recording):
            data = stream.read(CHUNK)
            frames.append(data)
        print("Finished recording")
        stream.stop_stream()
        stream.close()
        p.terminate()
        to_atm(frames, "C:/Users/maxim/Downloads/")

    def fft(self):
        global fourier_frames
        fourier_frames = []
        global frames
        print("Calculating Fourier Transform...")
        for i in range(0, len(frames)):
            fourier = rfft(frames[i])
            fourier_frames.append(fourier)
        print("Finished Fourier Transform")


class Reproductor(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        top_frame = tk.Frame(self, width=200, height=400, bg='grey')
        label = ttk.Label(top_frame, text="Reproductor", font="Consolas")
        top_frame.grid(row=0, column=0, padx=10, pady=5)
        label.grid(row=0, column=0, padx=10, pady=10)

        play_audio_button = ttk.Button(
            top_frame,
            text='Play audio',
            compound=tk.LEFT,
            command=lambda: self.play_audio()
        )
        play_audio_button.grid(row=0, column=1, padx=10, pady=10)

        self.audio_pos = 0
        self.play_audio_thread = None
        self.isPlaying = False

        self.frame1 = tk.Frame(self)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame1)

        self.frame1.grid(row=4, column=0, padx=10, pady=10)
        self.canvas.get_tk_widget().grid(row=5, column=0, padx=10, pady=10)

    def play_audio(self):
        global frames
        global external_wav_path
        print("Playing audio...")
        self.isPlaying = True
        p = pyaudio.PyAudio()
        wf = wave.open(external_wav_path, 'rb')
        print("wf.getnframes(): " + str(wf.getnframes()))
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        chunk = 1024

        data = wf.readframes(chunk)

        while data != b'' and self.isPlaying:
            stream.write(data)
            data = wf.readframes(chunk)
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Finished playing audio...")

    def play_audio_thread(self):
        self.play_audio_thread = threading.Thread(target=self.play_audio)
        self.play_audio_thread.start()


ventana = Autrumn()
ventana.mainloop()
