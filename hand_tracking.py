import cv2
import mediapipe as mp

# Khởi tạo thư viện MediaPipe để nhận diện tay
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)

# Mở webcam
cap = cv2.VideoCapture(0)
print("Đang chạy... Bấm phím 'q' trên cửa sổ camera để THOÁT.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Lật ảnh tạo hiệu ứng gương và chuyển sang RGB
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Nhận diện vị trí bàn tay
    results = hands.process(rgb_frame)

    # Nếu thấy tay thì vẽ khung xương lên màn hình
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Hiển thị kết quả ra màn hình
    cv2.imshow("Hand Tracking Window", frame)

    # Bấm 'q' để tắt
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()