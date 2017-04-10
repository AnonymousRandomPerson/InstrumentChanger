import numpy as np
import queue

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pylab as plt

# Whether to plot the returned signals.
debug = False

class Instrument:
    """A synthesized instrument."""
    
    def matchNotes(self, fileData, sampleRate):
        """
        Creates a musical excerpt that attempts to match the notes of the given audio data on the instrument.

        Args:
            fileData: The audio data to match.
            sampleRate: The sample rate to create audio for.

        Returns:
            A list of samples that match the notes in the given audio data.
        """
        samples = self.getNote(440, len(fileData), sampleRate)

        samples = self.duplicateChannel(samples)
        return samples

    def duplicateChannel(self, channel):
        """
        Duplicates a single channel of data into two channels.

        Args:
            channel: The single channel to duplicate.

        Returns:
            A double-channel list duplicated from the single channel
        """
        newSamples = []
        for sample in channel:
            sample32 = np.float32(sample / 2)
            newSamples.append((sample32, sample32))
        return newSamples

class Beep(Instrument):
    """A sine wave."""

    def getNote(self, frequency, duration, sampleRate):
        """
        Gets a note of a certain frequency.

        Args:
            frequency: The frequency of the note.
            duration: The duration of the note in samples.
            sampleRate: The sample rate to create audio for.

        Returns:
            A list of samples representing the note.
        """
        seconds = duration / sampleRate

        time = np.linspace(0, seconds, duration)
        samples = np.sin(frequency * 2 * np.pi * time)

        return samples

class AcousticGuitar(Instrument):
    """A synthesized acoustic guitar."""

    def getBaseStringSound(self, frequency, duration, sampleRate):
        """
        Gets a plucked string note without any distortion effects.

        Args:
            frequency: The frequency of the note.
            duration: The duration of the note in samples.

        Returns:
            A list of samples representing the note.
        """
        samples = []

        # Karplus-Strong algorithm, subtractive synthesis from white noise
        buffer = np.random.standard_normal(int(sampleRate / frequency))
        last = buffer[0]
        # Delay effect
        delayLine = queue.Queue(maxsize = 200)
        bufferCounter = 0
        for i in range(0, duration):
            # Low-pass filter
            current = (last + buffer[bufferCounter]) / 2
            if delayLine.full():
                delayed = delayLine.get()
                delayed *= 0.999
                # Feedback system
                current += delayed
                current /= 2

            samples.append(current)
            delayLine.put(current)
            last = current
            buffer[bufferCounter] = current

            bufferCounter += 1
            if bufferCounter >= len(buffer):
                bufferCounter = 0
        
        if debug:
            seconds = duration / sampleRate
            time = np.linspace(0, seconds, duration)
            plt.plot(time, samples)
            plt.show()

        return samples

    def getNote(self, frequency, duration, sampleRate):
        """
        Gets a note of a certain frequency.

        Args:
            frequency: The frequency of the note.
            duration: The duration of the note in samples.

        Returns:
            A list of samples representing the note.
        """
        samples = self.getBaseStringSound(frequency, duration, sampleRate)

        return samples

class Trumpet(Instrument):
    """A synthesized trumpet."""

    def getNote(self, frequency, duration, sampleRate):
        """
        Gets a note of a certain frequency.

        Args:
            frequency: The frequency of the note.
            duration: The duration of the note in samples.

        Returns:
            A list of samples representing the note.
        """
        seconds = duration / sampleRate

        # Additive synthesis
        envelope = [3.6, 2.825, 3, 2.688, 1.464, 1.520, 1.122, 0.940, 0.738, 0.495, 0.362, 0.237, 0.154, 0.154, 0.101, 0.082, 0.054, 0.038, 0.036]

        time = np.linspace(0, seconds, duration)
        samples = np.zeros(duration)
        for i, amplitude in enumerate(envelope):
            samples += amplitude * np.sin(frequency * (i + 1) * 2 * np.pi * time)

        # High-pass filter
        RC = 1 / (np.pi * frequency * 32)
        alpha = RC / (RC + 1.0 / sampleRate)
        newSamples = np.zeros(duration)
        newSamples[0] = samples[0]
        for i in range(1, duration):
            newSamples[i] = alpha * (newSamples[i - 1] + samples[i] - samples[i - 1])
        samples = newSamples

        # ADSR curve
        attackLength = int(0.075 * sampleRate)
        decayLength = int(0.3 * sampleRate)
        releaseLength = int(0.2 * sampleRate)
        sustainLength = duration - attackLength - decayLength - releaseLength

        if sustainLength >= 0:
            peak = 0.1
            sustain = peak * 0.8

            adsr = np.linspace(0, peak, attackLength)
            adsr = np.append(adsr, np.linspace(peak, sustain, decayLength))
            adsr = np.append(adsr, np.full(sustainLength, sustain))
            adsr = np.append(adsr, np.linspace(sustain, 0, releaseLength))

            samples *= adsr

        return samples