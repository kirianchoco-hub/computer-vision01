import open3d as o3d
import cv2
import mediapipe as mp
import math
import random
import numpy as np

# ==============================================================================
# I. CÁC HÀM KHỞI TẠO ĐỒ HỌA 3D (MESH HÌNH HỌC) - KÍCH THƯỚC SIÊU LỚN
# ==============================================================================

def create_blue_car(is_crashed=False):
    """Khởi tạo mô hình xe thể thao - Kích thước khổng lồ, đổi màu khi nổ máy"""
    car = o3d.geometry.TriangleMesh()
    
    body_color = [0.8, 0.1, 0.1] if is_crashed else [0.0, 0.4, 0.9]
    cabin_color = [0.1, 0.1, 0.1] if is_crashed else [0.15, 0.15, 0.15]
    
    # Thân siêu xe chính (width=1.1, height=1.8)
    body = o3d.geometry.TriangleMesh.create_box(width=1.1, height=1.8, depth=0.45)
    body.paint_uniform_color(body_color)  
    body.translate([-0.55, -0.9, 0.225])        
    car += body

    # Buồng lái kính xám đen
    cabin = o3d.geometry.TriangleMesh.create_box(width=0.8, height=0.9, depth=0.35)
    cabin.paint_uniform_color(cabin_color)
    cabin.translate([-0.4, -0.22, 0.675])
    car += cabin

    # 4 Bánh xe béo lớn (radius=0.22, height=0.15)
    def make_wheel(x, y, z):
        wheel = o3d.geometry.TriangleMesh.create_cylinder(radius=0.22, height=0.15)
        wheel.paint_uniform_color([0.15, 0.15, 0.15]) 
        R = wheel.get_rotation_matrix_from_xyz((0, math.pi / 2, 0))
        wheel.rotate(R, center=(0, 0, 0))
        wheel.translate([x, y, z])
        return wheel

    car += make_wheel(-0.62,  0.6, 0.22)  
    car += make_wheel( 0.47,  0.6, 0.22)  
    car += make_wheel(-0.62, -0.6, 0.22)  
    car += make_wheel( 0.47, -0.6, 0.22)  

    return car

def create_tree_obstacle():
    """Khởi tạo chướng ngại vật Cây thông cổ thụ khổng lồ"""
    tree = o3d.geometry.TriangleMesh()
    
    trunk = o3d.geometry.TriangleMesh.create_cylinder(radius=0.12, height=0.6)
    trunk.paint_uniform_color([0.4, 0.2, 0.05])
    trunk.translate([0, 0, 0.3])
    tree += trunk

    leaves1 = o3d.geometry.TriangleMesh.create_cone(radius=0.9, height=1.2)
    leaves1.paint_uniform_color([0.05, 0.4, 0.15])
    leaves1.translate([0, 0, 0.6])
    tree += leaves1

    return tree

# ==============================================================================
# II. CẤU HÌNH AI & KHỞI TẠO MÔI TRƯỜNG ĐƯỜNG ĐUA SIÊU RỘNG
# ==============================================================================

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2, 
    model_complexity=0, 
    min_detection_confidence=0.3, 
    min_tracking_confidence=0.3
)

# Biến cờ kiểm soát trạng thái thoát cưỡng bức toàn hệ thống
should_exit = False

def force_exit_callback(vis):
    """Hàm callback xử lý khi bấm nút thoát trên cửa sổ Open3D"""
    global should_exit
    should_exit = True
    return False

vis = o3d.visualization.VisualizerWithKeyCallback()
vis.create_window(window_name="Super Racing 3D - MAX SCALE", width=1280, height=800)

# Đăng ký phím trên cửa sổ Open3D: Phím Enter (13), Phím ESC (27), Phím Q (81 và 113)
vis.register_key_callback(13, force_exit_callback)
vis.register_key_callback(27, force_exit_callback)
vis.register_key_callback(81, force_exit_callback)
vis.register_key_callback(113, force_exit_callback)

# Đường nhựa siêu rộng 8.0
road_width = 8.0
road_mesh = o3d.geometry.TriangleMesh.create_box(width=road_width, height=60.0, depth=0.01)
road_mesh.paint_uniform_color([0.1, 0.1, 0.1]) 
road_mesh.translate([-road_width/2, -5.0, 0.0]) 
vis.add_geometry(road_mesh)

# Thảm cỏ nền hai bên đường
left_grass = o3d.geometry.TriangleMesh.create_box(width=15.0, height=60.0, depth=0.005)
left_grass.paint_uniform_color([0.12, 0.4, 0.12])
left_grass.translate([-(15.0 + road_width/2), -5.0, 0.0]) 
vis.add_geometry(left_grass)

right_grass = o3d.geometry.TriangleMesh.create_box(width=15.0, height=60.0, depth=0.005)
right_grass.paint_uniform_color([0.12, 0.4, 0.12])
right_grass.translate([road_width/2, -5.0, 0.0])  
vis.add_geometry(right_grass)

# Hệ thống vạch kẻ đường lớn hơn
road_lines = []
line_positions_y = []
for i in range(8):
    line = o3d.geometry.TriangleMesh.create_box(width=0.12, height=3.0, depth=0.015)
    line.paint_uniform_color([0.85, 0.75, 0.1])
    y_pos = i * 8.0 - 5.0
    line.translate([0.0, y_pos, 0.0])
    vis.add_geometry(line)
    road_lines.append(line)
    line_positions_y.append(y_pos)

car_mesh = create_blue_car(is_crashed=False)
vis.add_geometry(car_mesh)

obstacles = []
obstacle_types = []
obstacle_positions = []
num_obstacles = 4 

def spawn_all_obstacles():
    """Hàm phụ dùng để rải hoặc reset toàn bộ vật cản về trạng thái ban đầu"""
    global obstacle_positions
    obstacle_positions.clear()
    for idx, obs_mesh in enumerate(obstacles):
        obs_type = obstacle_types[idx]
        new_x = random.uniform(-3.3, 3.3)
        new_y = random.uniform(20.0 + idx * 12.0, 30.0 + idx * 15.0)
        
        obs_mesh.translate([-obs_mesh.get_center()[0], -obs_mesh.get_center()[1], 0])
        
        if obs_type == "box":
            obs_mesh.translate([new_x, new_y, 0.4]) 
        else:
            obs_mesh.translate([new_x, new_y, 0.0])
            
        obstacle_positions.append([new_x, new_y])

for i in range(num_obstacles):
    obs_type = random.choice(["box", "tree"])
    if obs_type == "box":
        obs_mesh = o3d.geometry.TriangleMesh.create_box(width=1.3, height=1.3, depth=1.1)
        obs_mesh.paint_uniform_color([0.75, 0.4, 0.1])
        obs_mesh.translate([-0.65, -0.65, 0.0])
    else:
        obs_mesh = create_tree_obstacle()

    vis.add_geometry(obs_mesh)
    obstacles.append(obs_mesh)
    obstacle_types.append(obs_type)

spawn_all_obstacles()

# ==============================================================================
# III. ĐIỀU CHỈNH GÓC NHÌN CAMERA ÁP SÁT MẶT ĐƯỜNG (XÓA PHẦN TRẮNG CHUẨN)
# ==============================================================================
view_ctl = vis.get_view_control()
view_ctl.set_front([0.0, 0.0, -1.0])  
view_ctl.set_up([0.0, 1.0, 0.0])     
vis.reset_view_point(True)

view_ctl.set_zoom(0.43)               
view_ctl.set_lookat([0.0, 7.0, 0.0])  

# ==============================================================================
# IV. MẠCH LOGIC VẬN HÀNH CHÍNH & VÒNG LẶP TRÒ CHƠI (MAIN LOOP)
# ==============================================================================

cap = cv2.VideoCapture(0)
car_x = 0.0
base_speed = 0.32
smooth_steering_angle = 0.0
game_over = False
flash_counter = 0  

print("\n=== ĐƯỜNG ĐUA SIÊU TO KHỔNG LỒ ===")
print(">> CÀI ĐẶT THOÁT KHẨN CẤP KHÓA CỨNG:")
print("👉 Cách 1: Nhấp chuột vào màn hình Camera đen -> Nhấn phím ENTER hoặc ESC hoặc phím Q")
print("👉 Cách 2: Nhấp chuột vào màn hình Game 3D -> Nhấn phím ENTER hoặc ESC hoặc phím Q")

while cap.isOpened() and not should_exit:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1) 
    h, w, c = frame.shape
    flash_counter += 1

    # Nới rộng vùng định vị an toàn (Safe Zone)
    box_left_top_left = (5, 60)
    box_left_bot_right = (320, 450)
    box_right_top_left = (w - 320, 60)
    box_right_bot_right = (w - 5, 450)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    left_hand_pt, right_hand_pt = None, None
    left_hand_in_zone, right_hand_in_zone = False, False

    if results.multi_hand_landmarks and not game_over:
        for hand_landmarks in results.multi_hand_landmarks:
            xs = [lm.x for lm in hand_landmarks.landmark]
            ys = [lm.y for lm in hand_landmarks.landmark]
            cx, cy = int(np.mean(xs) * w), int(np.mean(ys) * h)

            # Vẽ xương bàn tay
            for lm in hand_landmarks.landmark:
                lx, ly = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (lx, ly), 3, (0, 255, 255), -1)

            if box_left_top_left[0] <= cx <= box_left_bot_right[0] and box_left_top_left[1] <= cy <= box_left_bot_right[1]:
                left_hand_pt = (cx, cy)
                left_hand_in_zone = True
                cv2.circle(frame, (cx, cy), 15, (255, 0, 0), -1)
            elif box_right_top_left[0] <= cx <= box_right_bot_right[0] and box_right_top_left[1] <= cy <= box_right_bot_right[1]:
                right_hand_pt = (cx, cy)
                right_hand_in_zone = True
                cv2.circle(frame, (cx, cy), 15, (0, 0, 255), -1)

    hands_valid = left_hand_in_zone and right_hand_in_zone
    box_color = (0, 255, 0) if hands_valid else (0, 0, 255)
    cv2.rectangle(frame, box_left_top_left, box_left_bot_right, box_color, 3)
    cv2.rectangle(frame, box_right_top_left, box_right_bot_right, box_color, 3)

    if hands_valid and not game_over:
        dx = right_hand_pt[0] - left_hand_pt[0]
        dy = right_hand_pt[1] - left_hand_pt[1]
        raw_steering_angle = math.degrees(math.atan2(dy, dx))
        smooth_steering_angle = 0.5 * smooth_steering_angle + 0.5 * raw_steering_angle

        if smooth_steering_angle < -5 and car_x > -3.4:
            car_x -= 0.16
        elif smooth_steering_angle > 5 and car_x < 3.4:
            car_x += 0.16

        cv2.line(frame, left_hand_pt, right_hand_pt, (0, 255, 255), 4)
        cv2.putText(frame, f"Steering: {int(smooth_steering_angle)} deg", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
    elif not game_over:
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 69, 255), -1)
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        
        if (flash_counter // 7) % 2 == 0:
            cv2.putText(frame, "WARNING: HANDS OUT OF ZONE!", (w // 2 - 260, h // 2 - 20),
                        cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 255), 3)
            cv2.putText(frame, "Bring hands back to GREEN boxes to Resume", (w // 2 - 250, h // 2 + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    if game_over:
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 180), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        cv2.putText(frame, "GAME OVER", (w // 2 - 140, h // 2 - 20),
                    cv2.FONT_HERSHEY_DUPLEX, 1.8, (0, 0, 255), 5)
        cv2.putText(frame, "Press 'SPACE' to Restart", (w // 2 - 200, h // 2 + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    # --- CẬP NHẬT CHUYỂN ĐỘNG GAME 3D ---
    if hands_valid and not game_over:
        current_pos = car_mesh.get_center()
        car_mesh.translate([car_x - current_pos[0], 0.0, 0.0])

        for i in range(len(road_lines)):
            line_positions_y[i] -= base_speed
            road_lines[i].translate([0, -base_speed, 0])
            if line_positions_y[i] < -5.0:
                road_lines[i].translate([0, 64.0, 0])
                line_positions_y[i] += 64.0

        for i in range(num_obstacles):
            obstacle_positions[i][1] -= base_speed
            obstacles[i].translate([0, -base_speed, 0])

            obs_x = obstacle_positions[i][0]
            obs_y = obstacle_positions[i][1]

            if abs(car_x - obs_x) < 1.15 and abs(0.0 - obs_y) < 1.45:
                game_over = True
                vis.remove_geometry(car_mesh)
                car_mesh = create_blue_car(is_crashed=True)
                car_mesh.translate([car_x, 0.0, 0.0])
                vis.add_geometry(car_mesh)
                break

            if obstacle_positions[i][1] < -5.0:
                new_x = random.uniform(-3.3, 3.3)
                new_y = random.uniform(45.0, 55.0)
                obstacles[i].translate([new_x - obs_x, new_y - obs_y, 0])
                obstacle_positions[i] = [new_x, new_y]

    vis.update_geometry(car_mesh)
    for line in road_lines:
        vis.update_geometry(line)
    for obs in obstacles:
        vis.update_geometry(obs)
        
    # Nếu tắt cửa sổ bằng dấu X, vòng lặp dừng ngay lập tức
    if not vis.poll_events():
        break
    vis.update_renderer()

    # Hiển thị HUD Camera
    cv2.imshow("Hand Tracking HUD", frame)

    # ĐỌC PHÍM BẤM TRÊN CỬA SỔ CAMERA (CHỐNG TRÔI LỆNH)
    key = cv2.waitKey(1) & 0xFF
    
    # Chấp nhận mã phím Enter (13 hoặc 10), ESC (27), hoặc phím 'q' (113) / 'Q' (81)
    if key in [13, 10, 27, 113, 81]:
        break

    # Nhấn SPACE (32) để hồi sinh khi Game Over
    if key == 32 and game_over:
        car_x = 0.0
        game_over = False
        vis.remove_geometry(car_mesh)
        car_mesh = create_blue_car(is_crashed=False)
        vis.add_geometry(car_mesh)
        spawn_all_obstacles()

# Giải phóng và hủy toàn bộ tài nguyên hệ thống
cap.release()
cv2.destroyAllWindows()
vis.destroy_window()
print("\n>> ĐÃ THOÁT GAME THÀNH CÔNG VÀ AN TOÀN!")