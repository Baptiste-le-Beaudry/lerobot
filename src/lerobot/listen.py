import queue
import sounddevice as sd
import vosk
import json
import threading
import time


class SimpleSwitchDetector:
    def __init__(self, model_path="model-fr"):
        self.model = vosk.Model(model_path)
        self.q = queue.Queue()
        self.rec = vosk.KaldiRecognizer(self.model, 16000)
        self.stream = None
        self.switch_detected = False
        self.listening = False
        
    def callback(self, indata, frames, time, status):
        self.q.put(bytes(indata))
    
    def start_listening(self):
        if self.listening:
            return
        
        self.stream = sd.InputStream(
            samplerate=16000, 
            channels=1, 
            callback=self.callback
        )
        self.stream.start()
        self.listening = True
        
        # Thread pour traiter l'audio
        threading.Thread(target=self._process_audio, daemon=True).start()
        print("🎤 Écoute du mot 'switch'...")
    
    def _process_audio(self):
        while self.listening:
            try:
                data = self.q.get(timeout=0.1)
                if self.rec.AcceptWaveform(data):
                    result = json.loads(self.rec.Result())
                    text = result.get('text', '').lower()
                    if 'switch' in text:
                        self.switch_detected = True
                        print(f"🔊 Switch détecté dans: '{text}'")
            except queue.Empty:
                continue
    
    def check_switch(self):
        """Retourne True si 'switch' a été dit, puis remet à False"""
        if self.switch_detected:
            self.switch_detected = False
            return True
        return False
    
    def stop_listening(self):
        self.listening = False
        if self.stream:
            self.stream.stop()
            self.stream.close()

# Utilisation simple
def create_voice_detector():
    """Crée et démarre le détecteur vocal"""
    detector = SimpleSwitchDetector()
    detector.start_listening()
    return detector

# Exemple d'intégration dans votre boucle existante
def example_usage():
    # Créer le détecteur
    voice_detector = create_voice_detector()
    
    try:
        # Dans votre boucle de record
        for i in range(100):  # Exemple de boucle
            # Vérifier si 'switch' a été dit
            if voice_detector.check_switch():
                print("🔄 Switch demandé !")
                # Votre logique de switch ici
            
            # Vos autres opérations...
            time.sleep(0.1)
            
    finally:
        voice_detector.stop_listening()

if __name__ == "__main__":
    example_usage()