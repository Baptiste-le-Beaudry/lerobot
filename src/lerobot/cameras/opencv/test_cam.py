import cv2
import signal
import sys

running = True
def signal_handler(sig, frame):
    global running
    running = False
signal.signal(signal.SIGINT, signal_handler)


camera_indices = [0, 1, 2]
caps = {}



for idx in camera_indices:
    cap = cv2.VideoCapture(idx)
    if cap.isOpened():
        print(f"Caméra trouvée à l’index {idx}")
        caps[idx] = cap
    else:
        cap.release()

if not caps:
    print("Aucune caméra détectée.")
    sys.exit(1)

# Boucle d’affichage continue
while running:
    for idx, cap in caps.items():
        ret, frame = cap.read()
        if ret:
            cv2.imshow(f"Camera {idx}", frame)


    if cv2.waitKey(1) == 27:  # Échap pour quitter aussi
        break
"""
import cv2
import signal
import sys

# Variable de contrôle
running = True

# Handler pour Ctrl+C
def signal_handler(sig, frame):
    global running
    print("Interruption par l'utilisateur (Ctrl+C)")
    running = False

signal.signal(signal.SIGINT, signal_handler)

# Ouverture de la caméra
index=1
cap = cv2.VideoCapture(index)
if not cap.isOpened():
    print(f"Impossible d’ouvrir la caméra à l’index {index} ")
    sys.exit(1)

# Boucle principale
while running:
    ret, frame = cap.read()
    if not ret:
        print("Échec de lecture depuis la caméra")
        break

    cv2.imshow("Caméra 2", frame)

    # Arrêter si on appuie sur ESC
    if cv2.waitKey(1) == 27:
        print("Arrêt par touche Échap")
        break

# Libération des ressources
cap.release()
cv2.destroyAllWindows()
"""