import audioop
import os
import platform
import traceback
import wave
import pyaudio

# Utilities

import imp
import os
import sys


def main_is_frozen():
    return (hasattr(sys, "frozen") or  # new py2exe
            hasattr(sys, "importers") or  # old py2exe
            imp.is_frozen("__main__"))  # tools/freeze


def get_main_dir():
    if main_is_frozen():
        return os.path.abspath(os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def which(program):
    def is_exe(fpath):
        if os.name == 'nt':
            return os.path.isfile(fpath) or os.path.isfile(fpath + ".exe") or os.path.isfile(fpath + ".bat")
        else:
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        program = os.path.realpath(program)
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            exe_file = os.path.realpath(exe_file)
            if is_exe(exe_file):
                return exe_file

    return None

# End Utilities

try:
    from pydub import AudioSegment
    from pydub.utils import make_chunks
except ImportError:
    AudioSegment = None

try:
    import thread
except ImportError:
    import _thread as thread


class SoundPlayer:
    def __init__(self, soundfile, parent=None):
        self.soundfile = soundfile
        self.isplaying = False
        self.time = 0  # current audio position in frames
        self.audio = pyaudio.PyAudio()
        self.pydubfile = None
        self.volume = 100

        if AudioSegment:
            if which("ffmpeg") is not None:
                AudioSegment.converter = which("ffmpeg")
            elif which("avconv") is not None:
                AudioSegment.converter = which("avconv")
            else:
                if platform.system() == "Windows":
                    AudioSegment.converter = os.path.join(get_main_dir(), "ffmpeg.exe")
                    #AudioSegment.converter = os.path.dirname(os.path.realpath(__file__)) + "\\ffmpeg.exe"
                else:
                    # TODO: Check if we have ffmpeg or avconv installed
                    AudioSegment.converter = "ffmpeg"

        try:
            if AudioSegment:
                print(self.soundfile)
                self.pydubfile = AudioSegment.from_file(self.soundfile, format=os.path.splitext(self.soundfile)[1][1:])
            else:
                self.wave_reference = wave.open(self.soundfile)

            self.isvalid = True

        except:
            traceback.print_exc()
            self.wave_reference = None
            self.isvalid = False

    def IsValid(self):
        return self.isvalid

    def Duration(self):
        if AudioSegment:
            return(self.pydubfile.duration_seconds)
        else:
            return float(self.wave_reference.getnframes()) / float(self.wave_reference.getframerate())

    def GetRMSAmplitude(self, time, sampleDur):
        if AudioSegment:
            return self.pydubfile[time*1000.0:(time+sampleDur)*1000.0].rms
        else:
            startframe = int(round(time * self.wave_reference.getframerate()))
            samplelen = int(round(sampleDur * self.wave_reference.getframerate()))
            self.wave_reference.setpos(startframe)
            frame = self.wave_reference.readframes(samplelen)
            width = self.wave_reference.getsampwidth()
            return audioop.rms(frame, width)

    def IsPlaying(self):
        return self.isplaying

    def SetCurTime(self, time):
        self.time = time

    def Stop(self):
        self.isplaying = False

    def CurrentTime(self):
        return self.time

    def SetVolume(self, volume):
        self.volume = volume

    def _play(self, start, length):
        self.isplaying = True
        if AudioSegment:
            millisecondchunk = 50 / 1000.0

            stream = self.audio.open(format=
                                     self.audio.get_format_from_width(self.pydubfile.sample_width),
                                     channels=self.pydubfile.channels,
                                     rate=self.pydubfile.frame_rate,
                                     output=True)

            playchunk = self.pydubfile[start*1000.0:(start+length)*1000.0] - (60 - (60 * (self.volume/100.0)))
            self.time = start
            for chunks in make_chunks(playchunk, millisecondchunk*1000):
                self.time += millisecondchunk
                stream.write(chunks._data)
                if not self.isplaying:
                    break
                if self.time >= start+length:
                    break
        else:
            startframe = int(round(start * self.wave_reference.getframerate()))
            samplelen = int(round(length * self.wave_reference.getframerate()))
            remaining = samplelen
            chunk = 1024
            try:
                self.wave_reference.setpos(startframe)
            except wave.Error:
                self.isplaying = False
                return
            stream = self.audio.open(format=
                                     self.audio.get_format_from_width(self.wave_reference.getsampwidth()),
                                     channels=self.wave_reference.getnchannels(),
                                     rate=self.wave_reference.getframerate(),
                                     output=True)
            # read data

            if remaining >= 1024:
                data = audioop.mul(self.wave_reference.readframes(chunk),self.wave_reference.getsampwidth(), self.volume/100.0)
                remaining -= chunk
            else:
                data = audioop.mul(self.wave_reference.readframes(remaining),self.wave_reference.getsampwidth(), self.volume/100.0)
                remaining = 0

            # play stream
            while len(data) > 0 and self.isplaying:
                stream.write(data)
                self.time = float(self.wave_reference.tell()) / float(self.wave_reference.getframerate())
                if remaining >= 1024:
                    data = audioop.mul(self.wave_reference.readframes(chunk),self.wave_reference.getsampwidth(), self.volume/100.0)
                    remaining -= chunk
                else:
                    data = audioop.mul(self.wave_reference.readframes(remaining),self.wave_reference.getsampwidth(), self.volume/100.0)
                    remaining = 0
        stream.close()
        self.isplaying = False

    def Play(self, arg):
        thread.start_new_thread(self._play, (0, self.Duration()))

    def PlaySegment(self, start, length, arg):
        if not self.isplaying:  # otherwise this get's kinda echo-y
            thread.start_new_thread(self._play, (start, length))