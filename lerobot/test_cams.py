import cv2

for idx in range(3):
    for api in [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_FFMPEG]:
        cap = cv2.VideoCapture(idx, api)
        ok, _ = cap.read()
        print(f"Index {idx} with API {api}: {'OK' if ok else 'FAIL'}")
        cap.release()
