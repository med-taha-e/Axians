import cv2
import mediapipe as mp
import time

# Initialiser MediaPipe pour la détection de visage
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

start_time = None 

# Créer un objet pour la détection de visage
with mp_face_detection.FaceDetection(
    model_selection=1, min_detection_confidence=0.5) as face_detection:
  # Ouvrir la webcam
  cap = cv2.VideoCapture(0)

  # Initialiser l'enregistrement vidéo
  fourcc = cv2.VideoWriter_fourcc(*'XVID')
  out = None

  while cap.isOpened():
    success, image = cap.read()
    if not success:
      print("Ignoring empty camera frame.")
      continue

    # Convertir l'image en RGB (nécessaire pour MediaPipe)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # Traiter l'image avec le modèle de détection de visage
    results = face_detection.process(image)

    # Convertir l'image en BGR pour OpenCV
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if results.detections:
      # Si un visage est détecté, démarrer l'enregistrement (si ce n'est pas déjà fait)
      if out is None:
        # Définir le nom du fichier de sortie et les dimensions de la vidéo
        filename = f"enregistrement_{time.strftime('%Y%m%d_%H%M%S')}.avi"
        out = cv2.VideoWriter(filename, fourcc, 20.0, (image.shape[1], image.shape[0]))
        start_time = time.time()

      # Dessiner les boîtes englobantes autour des visages détectés
      for detection in results.detections:
        mp_drawing.draw_detection(image, detection)
 
    if out is not None:
      # Arrêter l'enregistrement
      elapsed_time = time.time() - start_time
      if elapsed_time >= 5:
        out.release()
        out = None
        start_time = None  #
    # Écrire le cadre dans la vidéo si l'enregistrement est en cours
    if out is not None:
      out.write(image)

    # Afficher l'image avec les visages détectés
    cv2.imshow('MediaPipe Face Detection', image)
    if cv2.waitKey(5) & 0xFF == 27:
      break

  # Libérer les ressources
  #if out is not None:
  #  out.release()
  cap.release()