import os
import sounddevice as sd
import numpy as np
import soundfile as sf
import threading

VOICEMAIL_DIR = os.path.join(os.getcwd(), "Voicemails")
os.makedirs(VOICEMAIL_DIR, exist_ok=True)

RECORD_DEVICE_ID = 1
OUTPUT_DEVICE_ID = 11

SAMPLE_RATE = 44100
CHANNELS = 1

recording_data = []
is_recording = False
current_filename = None
stream = None
is_playing = False
playback_thread = None

def list_voicemails():
    voicemails = [v for v in os.listdir(VOICEMAIL_DIR) if v.lower().endswith(".wav")]
    if not voicemails:
        print("No voicemails found.")
    else:
        print("Available Voicemails:")
        for i, voicemail in enumerate(voicemails, 1):
            print(f"{i}. {voicemail}")
    return voicemails

def start_recording():
    global is_recording, recording_data, stream
    if is_recording:
        print("Already recording")
        return
    recording_data.clear()
    is_recording = True
    print("Recording, press s to stop.")

    def callback(indata, frames, time, status):
        if is_recording:
            recording_data.append(indata.copy())

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                            device=RECORD_DEVICE_ID, callback=callback)
    stream.start()

def stop_recording():
    global is_recording, stream
    if not is_recording:
        print("Not recording")
        return
    is_recording = False
    if stream and stream.active:
        stream.stop()
        stream.close()
    print("Recording stopped. save voicemail by pressing v")

def save_voicemail():
    global recording_data, current_filename
    if not recording_data:
        print("Nothing recorded save. Record first")
        return

    filename = input("Enter a filename (filename.wav): ").strip()
    if not filename.endswith(".wav"):
        filename += ".wav"
    filepath = os.path.join(VOICEMAIL_DIR, filename)
    if os.path.exists(filepath):
        print("Filename in use.")
        return

    full_data = np.concatenate(recording_data, axis=0)
    full_data_int16 = (full_data * 32767).astype(np.int16)

    with sf.SoundFile(filepath, mode='x', samplerate=SAMPLE_RATE, channels=CHANNELS, subtype='PCM_16') as file:
        file.write(full_data_int16)

    print("Voicemail saved")

def load_voicemail():
    global current_filename
    voicemails = list_voicemails()
    if not voicemails:
        return
    choice_str = input("Enter the index of the voicemail: ")
    if not choice_str.isdigit():
        print("Invalid")
        return
    choice = int(choice_str) - 1
    if 0 <= choice < len(voicemails):
        filepath = os.path.join(VOICEMAIL_DIR, voicemails[choice])
        current_filename = filepath
        print(f"Loaded voicemail: {voicemails[choice]}")
    else:
        print("Invalid.")

def playback():
    global is_playing
    try:
        data, samplerate = sf.read(current_filename)
    except Exception as e:
        print(f"Error reading file: {e}")
        is_playing = False
        return

    print(f"Playing voicemail: {os.path.basename(current_filename)}")
    is_playing = True
    sd.play(data, samplerate, device=OUTPUT_DEVICE_ID)
    sd.wait()
    if is_playing:
        print("Playback finished")
    is_playing = False

def play_voicemail():
    global playback_thread, is_playing
    if not current_filename:
        print("No voicemail loaded or saved. Load ('l') or record ('r') and save ('v') first.")
        return
    if is_playing:
        print("Already playing a voicemail. Type 'x' to stop.")
        return
    playback_thread = threading.Thread(target=playback)
    playback_thread.start()

def stop_playback():
    global is_playing
    if is_playing:
        sd.stop()
        is_playing = False
        print("Playback cancelled")
    else:
        print("Nothing in playback")

def main():
    print("Voicemail playback, open readme for setup")
    print("Commands:")
    print("r - Start recording")
    print("s - Stop recording")
    print("v - Save voicemail")
    print("l - Load a voicemail")
    print("p - Play the loaded voicemail")
    print("x - Stop playback")
    print("q - Quit")

    while True:
        cmd = input("Enter command: ").strip().lower()
        if cmd == 'r':
            start_recording()
        elif cmd == 's':
            stop_recording()
        elif cmd == 'v':
            save_voicemail()
        elif cmd == 'l':
            load_voicemail()
        elif cmd == 'p':
            play_voicemail()
        elif cmd == 'x':
            stop_playback()
        elif cmd == 'q':
            print("Exiting")
            break
        else:
            print("Unknown command. usage: <-> r, s, v, l, p, x, q")

if __name__ == "__main__":
    main()
