// --- 1. KHỞI TẠO ĐỐI TƯỢNG AN TOÀN ---
const dino = document.getElementById("dino");
const cactus = document.getElementById("cactus");
const scoreElement = document.getElementById("score");
const gameOverScreen = document.getElementById("game-over-screen");
const finalScoreTxt = document.getElementById("final-score");

let score = 0;
let isGameOver = false;

// --- 2. LOGIC NHẢY (CẤU TRÚC ĐỘC LẬP KHÔNG SỢ SẬP) ---
document.addEventListener("keydown", function(event) {
    if ((event.code === "Space" || event.code === "ArrowUp") && !isGameOver) {
        if (dino && !dino.classList.contains("jump")) {
            dino.classList.add("jump");
            setTimeout(function() {
                dino.classList.remove("jump");
            }, 500); 
        }
    }
});

// --- 3. TÍNH ĐIỂM ---
if (cactus) {
    cactus.addEventListener('animationiteration', () => {
        if (!isGameOver && scoreElement) {
            score++;
            scoreElement.innerText = "Điểm: " + score;
        }
    });
}

// --- 4. BỘ QUÉT VA CHẠM THỜI GIAN THỰC ---
let checkCollision = setInterval(function() {
    if (isGameOver || !dino || !cactus) return;

    let dinoRect = dino.getBoundingClientRect();
    let cactusRect = cactus.getBoundingClientRect();

    if (
        dinoRect.right - 8 > cactusRect.left &&
        dinoRect.left + 8 < cactusRect.right &&
        dinoRect.bottom - 8 > cactusRect.top &&
        dinoRect.top + 8 < cactusRect.bottom
    ) {
        isGameOver = true;
        
        // Đóng băng chuyển động tại vị trí chạm
        cactus.style.animationPlayState = "paused";
        dino.style.animationPlayState = "paused";
        
        // Hiển thị giao diện kết thúc
        if (finalScoreTxt) finalScoreTxt.innerText = "Điểm của bạn: " + score;
        if (gameOverScreen) gameOverScreen.style.display = "block";
    }
}, 10);

// --- 5. HÀM CHƠI LẠI ---
function restartGame() {
    score = 0;
    if (scoreElement) scoreElement.innerText = "Điểm: 0";
    if (gameOverScreen) gameOverScreen.style.display = "none";
    
    if (cactus && dino) {
        cactus.style.animationPlayState = "running";
        dino.style.animationPlayState = "running";
        
        cactus.classList.remove("cactus-move");
        void cactus.offsetWidth; 
        cactus.classList.add("cactus-move");
    }
    
    isGameOver = false;
}

// --- 6. HÀM GỬI ĐÁNH GIÁ NGẦM LÊN GOOGLE FORM ---
function submitFeedbackSilently() {
    let token = localStorage.getItem("device_token");
    if (!token) {
        token = 'user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem("device_token", token);
    }

    const ratingSelect = document.getElementById("rating-select");
    const userRating = ratingSelect ? ratingSelect.value : "10";

    const formActionUrl = "https://docs.google.com/forms/d/e/1FAIpQLScd-EK9_UZUCp_SRXrcvbwo29gY9nCY9N3Qj7OdO5RaC_xzgQ/formResponse";
    const formData = new FormData();
    
    // Khớp chính xác ID Form của bạn
    formData.append("entry.833317391", token);       // Cột Token
    formData.append("entry.807109699", userRating);  // Cột Điểm số

    fetch(formActionUrl, {
        method: "POST",
        body: formData,
        mode: "no-cors"
    })
    .then(() => {
        alert("Cảm ơn bạn đã gửi đánh giá thành công!");
        restartGame();
    })
    .catch((error) => {
        console.error("Lỗi:", error);
        alert("Gửi thất bại, vui lòng thử lại.");
    });
}