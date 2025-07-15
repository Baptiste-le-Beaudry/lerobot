import cv2

for idx in range(3):
    for api in [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_FFMPEG]:
        cap = cv2.VideoCapture(idx, api)
        ok, _ = cap.read()
        print(f"Index {idx} with API {api}: {'OK' if ok else 'FAIL'}")
        cap.release()
import cv2

# Indices ou chemins des caméras
cameras = {
    "front": 2,   # ou 0 selon ta config
    "wrist": 0,   # ou 2 selon ta config
}

# Dictionnaire pour stocker les objets VideoCapture
captures = {}

# Initialisation des flux
for name, index in cameras.items():
    cap = cv2.VideoCapture(index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    if not cap.isOpened():
        print(f"[ERREUR] Caméra '{name}' (index {index}) introuvable.")
    captures[name] = cap

print("[INFO] Appuyez sur 'q' pour quitter.")

while True:
    for name, cap in captures.items():
        ret, frame = cap.read()
        if ret:
            cv2.imshow(f"Camera: {name}", frame)
        else:
            print(f"[ERREUR] Impossible de lire la caméra '{name}'")

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libération des ressources
for cap in captures.values():
    cap.release()
cv2.destroyAllWindows()
