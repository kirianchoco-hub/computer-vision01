import cv2
import mediapipe as mp
import numpy as np
import math

# ==============================================================================
# I. KHỞI TẠO AI & CẤU HÌNH NHẬN DIỆN MỞ RỘNG TOÀN KHUNG HÌNH
# ==============================================================================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,              
    model_complexity=1,           
    min_detection_confidence=0.5, 
    min_tracking_confidence=0.5
)

width, height = 1280, 720
header_height = 100  # Ranh giới thanh công cụ

# Khởi tạo Bảng trắng
whiteboard = np.ones((height, width, 3), dtype=np.uint8) * 255

colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 255)]
color_index = 0       
brush_thickness = 6
eraser_thickness = 60

xp, yp = None, None

# --- BIẾN NGƯỠNG ĐO CHIỀU DÀI NGÓN TAY ---
calibrated = False       
calib_frames = 0         
calib_data = []          
saved_threshold = 0  

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

print("\n=== 🖌️ BẢNG VIẾT ẢO - ĐÃ THÊM KHUNG PHÂN VÙNG VẼ VÀ FIX LỖI XÓA VIỀN ===")
print("👉 Hệ thống đã đóng khung nét đứt khu vực DRAWING ZONE để bạn dễ định vị.")
print("👉 Cục tẩy hiện tại đã có thể xóa sát mép menu mà không bị kẹt nét vẽ.")
print(">> Phím 'R': Đo lại tay | ENTER hoặc ESC: Thoát.")

# ==============================================================================
# II. VÒNG LẶP XỬ LÝ CHÍNH (MAIN LOOP)
# ==============================================================================
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    
    frame = cv2.flip(frame, 1) 
    frame = cv2.resize(frame, (width, height)) 

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # 1. THIẾT KẾ UI HEADER CỐ ĐỊNH (Thanh Menu)
    cv2.rectangle(frame, (0, 0), (width, header_height), (220, 220, 220), cv2.FILLED)
    for i, col in enumerate(colors[:3]):
        cv2.rectangle(frame, (40 + i*250, 15), (240 + i*250, 85), col, cv2.FILLED)
    cv2.rectangle(frame, (790, 15), (990, 85), (255, 255, 255), cv2.FILLED)
    cv2.rectangle(frame, (790, 15), (990, 85), (0, 0, 0), 2)
    cv2.putText(frame, "ERASER", (855, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    # 2. ĐÁNH DẤU KHU VỰC VẼ ĐƯỢC (DRAWING ZONE ACTIVE) BẰNG KHUNG NÉT ĐỨT
    # Khung này xuất hiện trên cả cửa sổ camera và bảng trắng để bạn dễ quan sát viền viết
    for y_dash in range(header_height, height, 20):
        # Đường biên dọc bên trái và bên phải
        cv2.line(frame, (5, y_dash), (5, y_dash + 10), (180, 180, 180), 2)
        cv2.line(frame, (width - 5, y_dash), (width - 5, y_dash + 10), (180, 180, 180), 2)
        cv2.line(whiteboard, (5, y_dash), (5, y_dash + 10), (220, 220, 220), 1)
        cv2.line(whiteboard, (width - 5, y_dash), (width - 5, y_dash + 10), (220, 220, 220), 1)
        
    for x_dash in range(0, width, 20):
        # Đường biên ngang ngay sát dưới thanh Menu công cụ và dưới đáy khung hình
        cv2.line(frame, (x_dash, header_height + 2), (x_dash + 10, header_height + 2), (150, 150, 150), 2)
        cv2.line(frame, (x_dash, height - 5), (x_dash + 10, height - 5), (180, 180, 180), 2)
        cv2.line(whiteboard, (x_dash, header_height + 2), (x_dash + 10, header_height + 2), (200, 200, 200), 1)
        cv2.line(whiteboard, (x_dash, height - 5), (x_dash + 10, height - 5), (220, 220, 220), 1)

    status_text = "MODE: STANDBY"
    status_color = (128, 128, 128)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            lm_list = []
            for lm in hand_landmarks.landmark:
                # Thuật toán ép biên an toàn mở rộng 100% không gian camera
                cx = np.clip(int(lm.x * width), 0, width - 1)
                cy = np.clip(int(lm.y * height), 0, height - 1)
                lm_list.append([cx, cy])

            if len(lm_list) != 0:
                x5, y5 = lm_list[5][0], lm_list[5][1]
                x8, y8 = lm_list[8][0], lm_list[8][1] # Đầu ngón trỏ để vẽ và xóa

                # Tính tỷ lệ chiều dài thực tế ngón trỏ chống sai số khoảng cách xa gần
                current_finger_len = math.hypot(x8 - x5, y8 - y5)
                base_bone = math.hypot(lm_list[5][0] - lm_list[0][0], lm_list[5][1] - lm_list[0][1])
                finger_ratio = current_finger_len / base_bone if base_bone != 0 else 0

                # --- GIAI ĐOẠN CALIBRATION (LƯU THÔNG SỐ TAY) ---
                if not calibrated:
                    calib_frames += 1
                    calib_data.append(finger_ratio)
                    status_text = f"MEASURING FINGER TIGHT... ({int((calib_frames/30)*100)}%)"
                    status_color = (0, 165, 255)
                    cv2.line(frame, (x5, y5), (x8, y8), (255, 255, 0), 3)
                    
                    if calib_frames >= 30:
                        saved_threshold = np.mean(calib_data) * 0.84
                        calibrated = True
                        print(f">> Cấu hình vùng vẽ thành công! Ngưỡng ngón thẳng: {saved_threshold:.2f}")
                
                # --- GIAI ĐOẠN HOẠT ĐỘNG THỰC TẾ ---
                else:
                    finger_is_straight = finger_ratio >= saved_threshold

                    cv2.line(frame, (x5, y5), (x8, y8), (0, 255, 0), 2)
                    cv2.putText(frame, f"Len: {finger_ratio:.2f} / Min: {saved_threshold:.2f}", (x8 + 15, y8), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

                    if finger_is_straight:
                        # 🛠️ FIX LỖI CHỌN NHẦM MENU KHI XÓA SÁT BIÊN:
                        # Chỉ nhảy vào chế độ chọn Tool khi ngón tay đang dùng BÚT VẼ (color_index != 3) 
                        # Hoặc khi ngón tay đâm hẳn sâu lên phía trên (y8 < 75).
                        if y8 < header_height and (color_index != 3 or y8 < 75):
                            xp, yp = None, None
                            cv2.circle(frame, (x8, y8), 15, (255, 255, 255), cv2.FILLED)
                            
                            if 40 < x8 < 240: color_index = 0
                            elif 290 < x8 < 490: color_index = 1
                            elif 540 < x8 < 740: color_index = 2
                            elif 790 < x8 < 990: color_index = 3
                            status_text = "SELECTING TOOL..."
                            status_color = (0, 0, 0)
                        
                        # Khu vực viết vẽ và xóa hoạt động tự do toàn không gian Drawing Zone
                        else:
                            draw_color = colors[color_index]
                            cam_circle_color = (150, 150, 150) if color_index == 3 else draw_color
                            cam_circle_radius = 25 if color_index == 3 else 10
                            cv2.circle(frame, (x8, y8), cam_circle_radius, cam_circle_color, cv2.FILLED)

                            if xp is None: xp, yp = x8, y8

                            if color_index == 3: 
                                # Cục tẩy được vẽ lấn lên sát mép menu để xóa sạch các đốm dính ở rìa
                                cv2.line(whiteboard, (xp, yp), (x8, y8), colors[color_index], eraser_thickness)
                                status_text = "MODE: ERASER (ACTIVE ZONE)"
                            else: 
                                # Bút vẽ chỉ được vẽ khi nằm hoàn toàn dưới thanh menu để tránh đè nét lên UI
                                if y8 > header_height:
                                    cv2.line(whiteboard, (xp, yp), (x8, y8), colors[color_index], brush_thickness)
                                status_text = "MODE: DRAWING"
                            
                            status_color = (0, 140, 255) if color_index == 3 else draw_color
                            xp, yp = x8, y8
                    else:
                        xp, yp = None, None
                        cv2.circle(frame, (x8, y8), 6, (0, 0, 255), cv2.FILLED)
                        status_text = "WRITING PAUSED"
                        status_color = (0, 0, 255)
    else:
        xp, yp = None, None

    # Hiển thị HUD thông báo trạng thái hoạt động ở đáy màn hình
    cv2.putText(frame, status_text, (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
    cv2.putText(frame, "DRAWING ZONE ACTIVE", (width - 260, height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

    cv2.imshow("1. Hand Tracking HUD (Camera Window)", frame)
    cv2.imshow("2. Pure Whiteboard (Output Window)", whiteboard)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('r') or key == ord('R'):
        calibrated = False
        calib_frames = 0
        calib_data = []
        print(">> Đang tái cấu hình vùng nhận diện ngón tay...")

    if key in [13, 10, 27]: # Phím ENTER hoặc ESC để THOÁT
        break
    if key == ord('c') or key == ord('C'):
        whiteboard = np.ones((height, width, 3), dtype=np.uint8) * 255
        print(">> Đã dọn sạch bảng vẽ!")

cap.release()
cv2.destroyAllWindows()