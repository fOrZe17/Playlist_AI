// Playlist AI — клиентская логика

const API = "/api";
const AUTH_API = "/api/auth";

// ===== УТИЛИТЫ =====

function getToken() {
    return localStorage.getItem("token");
}

function getEmail() {
    return localStorage.getItem("email");
}

function setAuth(token, email) {
    localStorage.setItem("token", token);
    localStorage.setItem("email", email);
}

function clearAuth() {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
}

function isLoggedIn() {
    return !!getToken();
}

function authHeaders() {
    return { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` };
}

// ===== TOAST =====

function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.3s";
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ===== НАВБАР =====

function updateNav() {
    const guestLinks = document.querySelectorAll(".nav-guest");
    const authBlock = document.getElementById("nav-auth");
    const emailSpan = document.getElementById("nav-email");

    if (isLoggedIn()) {
        guestLinks.forEach((el) => (el.style.display = "none"));
        if (authBlock) {
            authBlock.classList.add("visible");
            emailSpan.textContent = getEmail();
        }
    } else {
        guestLinks.forEach((el) => (el.style.display = ""));
        if (authBlock) authBlock.classList.remove("visible");
    }
}

// ===== КНОПКА ЗАГРУЗКИ =====

function setLoading(btn, loading) {
    if (!btn) return;
    if (loading) {
        btn.disabled = true;
        btn.dataset.originalText = btn.textContent;
        btn.innerHTML = '<span class="spinner"></span> Загрузка...';
    } else {
        btn.disabled = false;
        btn.textContent = btn.dataset.originalText || "Отправить";
    }
}

// ===== ПОКАЗАТЬ ОШИБКУ =====

function showFormError(msg) {
    const el = document.getElementById("form-error");
    if (!el) return;
    el.textContent = msg;
    el.style.display = "block";
}

function hideFormError() {
    const el = document.getElementById("form-error");
    if (el) el.style.display = "none";
}

// ===== РЕГИСТРАЦИЯ =====

function initRegister() {
    const form = document.getElementById("register-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideFormError();

        const email = form.email.value.trim();
        const password = form.password.value;
        const confirm = form.password_confirm.value;

        if (password !== confirm) {
            showFormError("Пароли не совпадают");
            return;
        }
        if (password.length < 4) {
            showFormError("Пароль должен быть не менее 4 символов");
            return;
        }

        const btn = document.getElementById("submit-btn");
        setLoading(btn, true);

        try {
            const res = await fetch(`${AUTH_API}/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const data = await res.json();
            if (!res.ok) {
                showFormError(data.detail || "Ошибка регистрации");
                return;
            }
            setAuth(data.token, data.email);
            showToast("Регистрация успешна!");
            setTimeout(() => (window.location.href = "/generate"), 500);
        } catch {
            showFormError("Ошибка сети");
        } finally {
            setLoading(btn, false);
        }
    });
}

// ===== ВХОД =====

function initLogin() {
    const form = document.getElementById("login-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideFormError();

        const email = form.email.value.trim();
        const password = form.password.value;

        const btn = document.getElementById("submit-btn");
        setLoading(btn, true);

        try {
            const res = await fetch(`${AUTH_API}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const data = await res.json();
            if (!res.ok) {
                showFormError(data.detail || "Ошибка входа");
                return;
            }
            setAuth(data.token, data.email);
            showToast("Вход выполнен!");
            setTimeout(() => (window.location.href = "/generate"), 500);
        } catch {
            showFormError("Ошибка сети");
        } finally {
            setLoading(btn, false);
        }
    });
}

// ===== ГЕНЕРАЦИЯ =====

function initGenerate() {
    const form = document.getElementById("generate-form");
    if (!form) return;

    // Счётчик символов (до проверки авторизации, чтобы работал всегда)
    const promptEl = document.getElementById("prompt");
    const charCount = document.getElementById("char-count");
    function updateCharCount() {
        if (charCount) charCount.textContent = promptEl.value.length;
    }
    promptEl.addEventListener("input", updateCharCount);
    updateCharCount();

    // Подсказки
    document.querySelectorAll(".prompt-hint").forEach((hint) => {
        hint.addEventListener("click", () => {
            promptEl.value = hint.dataset.prompt;
            updateCharCount();
        });
    });

    if (!isLoggedIn()) {
        showToast("Войдите для генерации плейлистов", "error");
        setTimeout(() => (window.location.href = "/login"), 1500);
        return;
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const prompt = form.prompt.value.trim();
        if (!prompt) return;

        const btn = document.getElementById("generate-btn");
        setLoading(btn, true);

        const resultBlock = document.getElementById("playlist-result");
        resultBlock.classList.remove("visible");

        try {
            const res = await fetch(`${API}/generate`, {
                method: "POST",
                headers: authHeaders(),
                body: JSON.stringify({ prompt, title: "" }),
            });

            if (res.status === 401) {
                showToast("Сессия истекла, войдите снова", "error");
                clearAuth();
                setTimeout(() => (window.location.href = "/login"), 1000);
                return;
            }

            const data = await res.json();
            if (!res.ok) {
                showToast(data.detail || "Ошибка генерации", "error");
                return;
            }

            renderPlaylist(data);
            showToast("Плейлист сгенерирован!");
        } catch {
            showToast("Ошибка сети", "error");
        } finally {
            setLoading(btn, false);
        }
    });
}

function renderPlaylist(playlist) {
    const resultBlock = document.getElementById("playlist-result");
    const titleEl = document.getElementById("playlist-title");
    const countEl = document.getElementById("track-count");
    const listEl = document.getElementById("track-list");

    titleEl.textContent = playlist.title;
    countEl.textContent = `${playlist.tracks.length} треков`;
    listEl.innerHTML = "";

    playlist.tracks.forEach((track, i) => {
        console.log("Track data:", track);

        const item = document.createElement("div");
        item.className = "track-item";
        item.style.animationDelay = `${i * 0.08}s`;

        // Номер трека
        const numberEl = document.createElement("span");
        numberEl.className = "track-number";
        numberEl.textContent = i + 1;
        item.appendChild(numberEl);

        // Обложка: картинка или эмодзи
        const coverValue = track.cover || "🎵";
        if (coverValue.startsWith("http")) {
            const img = document.createElement("img");
            img.className = "track-cover-img";
            img.src = coverValue;
            img.alt = track.title;
            item.appendChild(img);
        } else {
            const coverDiv = document.createElement("div");
            coverDiv.className = "track-cover";
            coverDiv.textContent = coverValue;
            item.appendChild(coverDiv);
        }

        // Информация о треке
        const infoDiv = document.createElement("div");
        infoDiv.className = "track-info";

        if (track.url) {
            const link = document.createElement("a");
            link.className = "track-title track-link";
            link.href = track.url;
            link.target = "_blank";
            link.rel = "noopener";
            link.textContent = track.title;
            infoDiv.appendChild(link);
        } else {
            const titleDiv = document.createElement("div");
            titleDiv.className = "track-title";
            titleDiv.textContent = track.title;
            infoDiv.appendChild(titleDiv);
        }

        const artistDiv = document.createElement("div");
        artistDiv.className = "track-artist";
        artistDiv.textContent = track.artist;
        infoDiv.appendChild(artistDiv);

        item.appendChild(infoDiv);

        // Длительность
        const durationEl = document.createElement("span");
        durationEl.className = "track-duration";
        durationEl.textContent = track.duration || "";
        item.appendChild(durationEl);

        listEl.appendChild(item);
    });

    resultBlock.classList.add("visible");
}

// ===== ПРОФИЛЬ =====

function initProfile() {
    if (!isLoggedIn()) {
        showToast("Войдите, чтобы просмотреть профиль", "error");
        setTimeout(() => (window.location.href = "/login"), 1500);
        return;
    }

    loadProfile();
    loadPlaylists();
}

async function loadProfile() {
    try {
        const res = await fetch(`${AUTH_API}/me`, { headers: authHeaders() });
        if (res.status === 401) {
            clearAuth();
            window.location.href = "/login";
            return;
        }
        const data = await res.json();

        const avatarEl = document.getElementById("profile-avatar");
        const emailEl = document.getElementById("profile-email");
        const dateEl = document.getElementById("profile-date");
        const statPlaylists = document.getElementById("stat-playlists");

        if (avatarEl) avatarEl.textContent = data.email.charAt(0).toUpperCase();
        if (emailEl) emailEl.textContent = data.email;
        if (dateEl) {
            const d = new Date(data.created_at);
            dateEl.textContent = `С ${d.toLocaleDateString("ru-RU")}`;
        }
        if (statPlaylists) statPlaylists.textContent = data.playlists_count;
    } catch {
        showToast("Ошибка загрузки профиля", "error");
    }
}

async function loadPlaylists() {
    try {
        const res = await fetch(`${API}/playlists`, { headers: authHeaders() });
        const data = await res.json();
        const container = document.getElementById("playlists-history");
        if (!container) return;

        const playlists = data.playlists || [];
        const statTracks = document.getElementById("stat-tracks");

        let totalTracks = 0;
        playlists.forEach((p) => (totalTracks += (p.tracks || []).length));
        if (statTracks) statTracks.textContent = totalTracks;

        if (playlists.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">&#127925;</span>
                    <p>Плейлисты пока не созданы</p>
                    <a href="/generate" class="btn">Создать первый</a>
                </div>`;
            return;
        }

        container.innerHTML = "";
        playlists.reverse().forEach((pl) => {
            const item = document.createElement("div");
            item.className = "history-item card";
            const d = new Date(pl.created_at);
            item.innerHTML = `
                <div>
                    <div class="history-title">${pl.title}</div>
                    <div class="history-meta">${d.toLocaleDateString("ru-RU")} &middot; ${pl.prompt.slice(0, 50)}</div>
                </div>
                <span class="history-tracks-count">${(pl.tracks || []).length} треков</span>
            `;
            container.appendChild(item);
        });
    } catch {
        showToast("Ошибка загрузки плейлистов", "error");
    }
}

// ===== ИНИЦИАЛИЗАЦИЯ =====

document.addEventListener("DOMContentLoaded", () => {
    updateNav();

    // Бургер-меню
    const burger = document.getElementById("nav-burger");
    const menu = document.getElementById("nav-menu");
    if (burger && menu) {
        burger.addEventListener("click", () => menu.classList.toggle("open"));
    }

    // Выход
    const logoutBtn = document.getElementById("btn-logout");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            clearAuth();
            showToast("Вы вышли из аккаунта");
            setTimeout(() => (window.location.href = "/"), 500);
        });
    }

    // Инициализация страниц
    initRegister();
    initLogin();
    initGenerate();

    if (document.querySelector(".profile-page")) {
        initProfile();
    }
});
