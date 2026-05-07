// Playlist AI — клиентская логика

const API = "/api";
const AUTH_API = "/api/auth";

let profilePlaylists = [];
let editingPlaylist = null;
let removedTrackIds = new Set();
let playlistSortMode = localStorage.getItem("playlistSortMode") || "date-new";
let playlistSearchQuery = "";
let playlistFavoritesOnly = false;
let pendingDeletePlaylist = null;

// ===== УТИЛИТЫ =====

function getToken() {
    return localStorage.getItem("token");
}

function getEmail() {
    return localStorage.getItem("email");
}

function getDisplayName() {
    return localStorage.getItem("displayName") || getEmail();
}

function getAvatarUrl() {
    return localStorage.getItem("avatarUrl");
}

function setUserProfile(email, displayName, avatarUrl) {
    localStorage.setItem("email", email);
    if (displayName) {
        localStorage.setItem("displayName", displayName);
    } else {
        localStorage.removeItem("displayName");
    }
    if (avatarUrl) {
        localStorage.setItem("avatarUrl", avatarUrl);
    } else {
        localStorage.removeItem("avatarUrl");
    }
}

function setAuth(token, email, displayName = null, avatarUrl = null) {
    localStorage.setItem("token", token);
    setUserProfile(email, displayName, avatarUrl);
}

function clearAuth() {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    localStorage.removeItem("displayName");
    localStorage.removeItem("avatarUrl");
}

function isLoggedIn() {
    return !!getToken();
}

function authHeaders() {
    return { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` };
}

function authOnlyHeaders() {
    return { Authorization: `Bearer ${getToken()}` };
}

function renderAvatar(element, name, avatarUrl) {
    if (!element) return;

    element.innerHTML = "";
    if (avatarUrl) {
        const img = document.createElement("img");
        img.src = avatarUrl;
        img.alt = name || "Avatar";
        element.appendChild(img);
        element.classList.add("has-image");
        return;
    }

    element.classList.remove("has-image");
    element.textContent = (name || "?").trim().charAt(0).toUpperCase() || "?";
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
    const navAvatar = document.getElementById("nav-avatar");

    if (isLoggedIn()) {
        guestLinks.forEach((el) => (el.style.display = "none"));
        if (authBlock) {
            authBlock.classList.add("visible");
            const name = getDisplayName();
            emailSpan.textContent = name;
            renderAvatar(navAvatar, name, getAvatarUrl());
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

function setGenerateLoading(btn, loading) {
    if (!btn) return;
    if (loading) {
        btn.disabled = true;
        btn.dataset.originalText = btn.textContent;
        btn.classList.add("btn-generating");
        btn.innerHTML = `
            <span class="generate-equalizer" aria-hidden="true">
                <span></span>
                <span></span>
                <span></span>
                <span></span>
            </span>
            <span>Собираю плейлист...</span>
        `;
    } else {
        btn.disabled = false;
        btn.classList.remove("btn-generating");
        btn.textContent = btn.dataset.originalText || "Сгенерировать";
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

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
    }[char]));
}

function pluralizeRu(count, one, few, many) {
    const absCount = Math.abs(Number(count));
    const lastTwo = absCount % 100;
    const lastOne = absCount % 10;

    if (lastTwo >= 11 && lastTwo <= 14) return many;
    if (lastOne === 1) return one;
    if (lastOne >= 2 && lastOne <= 4) return few;
    return many;
}

function formatTrackCount(count) {
    return `${count} ${pluralizeRu(count, "трек", "трека", "треков")}`;
}

function initPasswordReveal() {
    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        const field = button.closest(".password-field");
        const input = field ? field.querySelector("input") : null;
        if (!input) return;

        const reveal = () => {
            input.type = "text";
            button.classList.add("is-active");
        };
        const hide = () => {
            input.type = "password";
            button.classList.remove("is-active");
        };

        button.addEventListener("pointerdown", (e) => {
            e.preventDefault();
            button.setPointerCapture(e.pointerId);
            reveal();
        });
        button.addEventListener("pointerup", hide);
        button.addEventListener("pointercancel", hide);
        button.addEventListener("lostpointercapture", hide);
        button.addEventListener("blur", hide);
        button.addEventListener("keydown", (e) => {
            if (e.key === " " || e.key === "Enter") {
                e.preventDefault();
                reveal();
            }
        });
        button.addEventListener("keyup", hide);
    });
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
            setAuth(data.token, data.email, data.display_name, data.avatar_url);
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
            setAuth(data.token, data.email, data.display_name, data.avatar_url);
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
        setGenerateLoading(btn, true);

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
            setGenerateLoading(btn, false);
        }
    });
}

function renderPlaylist(playlist) {
    const resultBlock = document.getElementById("playlist-result");
    const titleEl = document.getElementById("playlist-title");
    const countEl = document.getElementById("track-count");
    const listEl = document.getElementById("track-list");

    titleEl.textContent = playlist.title;
    countEl.textContent = formatTrackCount(playlist.tracks.length);
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
        const emailSecondaryEl = document.getElementById("profile-email-secondary");
        const dateEl = document.getElementById("profile-date");
        const statPlaylists = document.getElementById("stat-playlists");
        const displayName = data.display_name || data.email;
        const fullName = [data.first_name, data.last_name].filter(Boolean).join(" ");

        setUserProfile(data.email, data.display_name, data.avatar_url);
        updateNav();

        renderAvatar(avatarEl, displayName, data.avatar_url);
        if (emailEl) emailEl.textContent = displayName;
        if (emailSecondaryEl) {
            const details = [];
            if (fullName) details.push(fullName);
            if (data.show_email) details.push(data.email);
            emailSecondaryEl.textContent = details.join(" · ");
            emailSecondaryEl.style.display = details.length ? "" : "none";
        }
        if (dateEl) {
            const d = new Date(data.created_at);
            dateEl.textContent = `С ${d.toLocaleDateString("ru-RU")}`;
            dateEl.style.display = data.show_created_at ? "" : "none";
        }
        if (statPlaylists) statPlaylists.textContent = data.playlists_count;
    } catch {
        showToast("Ошибка загрузки профиля", "error");
    }
}

async function loadProfileEdit() {
    const form = document.getElementById("profile-edit-form");
    if (!form) return;

    if (!isLoggedIn()) {
        showToast("Войдите, чтобы редактировать профиль", "error");
        setTimeout(() => (window.location.href = "/login"), 1000);
        return;
    }

    try {
        const res = await fetch(`${AUTH_API}/me`, { headers: authHeaders() });
        if (res.status === 401) {
            clearAuth();
            window.location.href = "/login";
            return;
        }

        const data = await res.json();
        const displayName = data.display_name || data.email;
        const nameInput = document.getElementById("display_name");
        const firstNameInput = document.getElementById("first_name");
        const lastNameInput = document.getElementById("last_name");
        const showEmailInput = document.getElementById("show_email");
        const showCreatedAtInput = document.getElementById("show_created_at");
        const emailEl = document.getElementById("profile-edit-email");
        const avatarPreview = document.getElementById("edit-avatar-preview");

        setUserProfile(data.email, data.display_name, data.avatar_url);
        updateNav();

        if (nameInput) nameInput.value = displayName;
        if (firstNameInput) firstNameInput.value = data.first_name || "";
        if (lastNameInput) lastNameInput.value = data.last_name || "";
        if (showEmailInput) showEmailInput.checked = data.show_email;
        if (showCreatedAtInput) showCreatedAtInput.checked = data.show_created_at;
        if (emailEl) emailEl.value = data.email;
        renderAvatar(avatarPreview, displayName, data.avatar_url);
    } catch {
        showFormError("Ошибка загрузки профиля");
    }
}

function initProfileEdit() {
    const form = document.getElementById("profile-edit-form");
    if (!form) return;

    const avatarInput = document.getElementById("avatar");
    const avatarPreview = document.getElementById("edit-avatar-preview");
    const nameInput = document.getElementById("display_name");
    const firstNameInput = document.getElementById("first_name");
    const lastNameInput = document.getElementById("last_name");
    const showEmailInput = document.getElementById("show_email");
    const showCreatedAtInput = document.getElementById("show_created_at");
    const currentPasswordInput = document.getElementById("current_password");
    const newPasswordInput = document.getElementById("new_password");
    const newPasswordConfirmInput = document.getElementById("new_password_confirm");

    loadProfileEdit();

    if (avatarInput) {
        avatarInput.addEventListener("change", () => {
            const file = avatarInput.files && avatarInput.files[0];
            if (!file) {
                renderAvatar(avatarPreview, nameInput.value || getDisplayName(), getAvatarUrl());
                return;
            }

            const previewUrl = URL.createObjectURL(file);
            renderAvatar(avatarPreview, nameInput.value || getDisplayName(), previewUrl);
        });
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideFormError();

        const displayName = nameInput.value.trim();
        if (displayName.length < 2) {
            showFormError("Имя пользователя должно быть не короче 2 символов");
            return;
        }

        const btn = document.getElementById("profile-edit-submit");
        const formData = new FormData();
        formData.append("display_name", displayName);
        formData.append("first_name", firstNameInput.value.trim());
        formData.append("last_name", lastNameInput.value.trim());
        formData.append("show_email", showEmailInput.checked ? "true" : "false");
        formData.append("show_created_at", showCreatedAtInput.checked ? "true" : "false");
        if (avatarInput.files && avatarInput.files[0]) {
            formData.append("avatar", avatarInput.files[0]);
        }

        const currentPassword = currentPasswordInput.value;
        const newPassword = newPasswordInput.value;
        const newPasswordConfirm = newPasswordConfirmInput.value;
        const wantsPasswordChange = currentPassword || newPassword || newPasswordConfirm;
        if (wantsPasswordChange) {
            if (!currentPassword || !newPassword || !newPasswordConfirm) {
                showFormError("Для смены пароля заполните все парольные поля");
                return;
            }
            if (newPassword !== newPasswordConfirm) {
                showFormError("Новые пароли не совпадают");
                return;
            }
            if (newPassword.length < 4) {
                showFormError("Новый пароль должен быть не менее 4 символов");
                return;
            }
        }

        setLoading(btn, true);
        try {
            const res = await fetch(`${AUTH_API}/profile`, {
                method: "PUT",
                headers: authOnlyHeaders(),
                body: formData,
            });

            if (res.status === 401) {
                clearAuth();
                window.location.href = "/login";
                return;
            }

            const data = await res.json();
            if (!res.ok) {
                showFormError(data.detail || "Ошибка сохранения профиля");
                return;
            }

            if (wantsPasswordChange) {
                const passwordRes = await fetch(`${AUTH_API}/password`, {
                    method: "PUT",
                    headers: authHeaders(),
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword,
                    }),
                });
                const passwordData = await passwordRes.json();
                if (!passwordRes.ok) {
                    showFormError(passwordData.detail || "Ошибка смены пароля");
                    return;
                }
            }

            setUserProfile(data.email, data.display_name, data.avatar_url);
            updateNav();
            renderAvatar(avatarPreview, data.display_name || data.email, data.avatar_url);
            showToast("Профиль сохранён");
            setTimeout(() => (window.location.href = "/profile"), 600);
        } catch {
            showFormError("Ошибка сети");
        } finally {
            setLoading(btn, false);
        }
    });
}

function ensurePlaylistEditorModal() {
    let modal = document.getElementById("playlist-editor-modal");
    if (modal) return modal;

    modal = document.createElement("div");
    modal.className = "playlist-modal";
    modal.id = "playlist-editor-modal";
    modal.setAttribute("aria-hidden", "true");
    modal.innerHTML = `
        <div class="playlist-modal-backdrop" data-modal-close></div>
        <div class="playlist-modal-panel" role="dialog" aria-modal="true" aria-labelledby="playlist-editor-title">
            <div class="playlist-modal-header">
                <div class="playlist-modal-title-row">
                    <h3 id="playlist-editor-title">Редактирование плейлиста</h3>
                    <button type="button" class="playlist-download-btn" id="download-playlist-csv" aria-label="Скачать CSV">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M12 3v11"></path>
                            <path d="m8 10 4 4 4-4"></path>
                            <path d="M5 17v2h14v-2"></path>
                        </svg>
                    </button>
                </div>
                <button type="button" class="modal-close-btn" data-modal-close aria-label="Закрыть">&times;</button>
            </div>
            <div class="form-group">
                <label for="edit-playlist-title">Название</label>
                <input type="text" id="edit-playlist-title" maxlength="255" required>
            </div>
            <div class="form-group">
                <label for="edit-playlist-prompt">Промпт</label>
                <input type="text" id="edit-playlist-prompt" disabled>
            </div>
            <div class="edit-track-summary" id="edit-track-summary"></div>
            <div class="edit-track-list" id="edit-track-list"></div>
            <div class="playlist-modal-actions">
                <button type="button" class="delete-playlist-btn" id="delete-playlist">Удалить плейлист</button>
                <div class="playlist-modal-save-actions">
                    <button type="button" class="btn btn-secondary" data-modal-close>Отмена</button>
                    <button type="button" class="btn" id="save-playlist-edit">Сохранить</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    return modal;
}

function ensureDeleteConfirmModal() {
    let modal = document.getElementById("delete-confirm-modal");
    if (modal) return modal;

    modal = document.createElement("div");
    modal.className = "confirm-modal";
    modal.id = "delete-confirm-modal";
    modal.setAttribute("aria-hidden", "true");
    modal.innerHTML = `
        <div class="confirm-modal-backdrop" data-delete-cancel></div>
        <div class="confirm-modal-panel" role="dialog" aria-modal="true" aria-labelledby="delete-confirm-title">
            <h3 id="delete-confirm-title">Удалить плейлист?</h3>
            <p id="delete-confirm-text"></p>
            <div class="confirm-modal-actions">
                <button type="button" class="btn btn-secondary" data-delete-cancel>Отмена</button>
                <button type="button" class="delete-playlist-btn" id="confirm-delete-playlist">Удалить</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    return modal;
}

function closePlaylistEditor() {
    const modal = document.getElementById("playlist-editor-modal");
    if (!modal) return;
    modal.classList.remove("visible");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
    editingPlaylist = null;
    removedTrackIds = new Set();
}

function openDeleteConfirm() {
    if (!editingPlaylist) return;

    pendingDeletePlaylist = editingPlaylist;
    const modal = ensureDeleteConfirmModal();
    const text = document.getElementById("delete-confirm-text");
    text.textContent = `Плейлист "${editingPlaylist.title}" будет удалён вместе со всеми треками. Это действие нельзя отменить.`;

    modal.classList.add("visible");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
    document.getElementById("confirm-delete-playlist").focus();
}

function closeDeleteConfirm() {
    const modal = document.getElementById("delete-confirm-modal");
    if (!modal) return;

    modal.classList.remove("visible");
    modal.setAttribute("aria-hidden", "true");
    pendingDeletePlaylist = null;

    const editorModal = document.getElementById("playlist-editor-modal");
    if (!editorModal || !editorModal.classList.contains("visible")) {
        document.body.classList.remove("modal-open");
    }
}

function getCsvTracks() {
    if (!editingPlaylist) return [];
    return (editingPlaylist.tracks || []).filter((track) => !removedTrackIds.has(track.id));
}

function escapeCsvValue(value) {
    const stringValue = String(value ?? "");
    return `"${stringValue.replace(/"/g, '""')}"`;
}

function formatPlaylistCsv(playlist, tracks) {
    const rows = [
        ["#", "Название", "Исполнитель", "Длительность", "Ссылка", "Промпт"],
        ...tracks.map((track, index) => [
            index + 1,
            track.title || "",
            track.artist || "",
            track.duration || "",
            track.url || "",
            playlist.prompt || "",
        ]),
    ];

    return [
        "sep=;",
        ...rows.map((row) => row.map(escapeCsvValue).join(";")),
    ].join("\r\n");
}

function downloadPlaylistCsv() {
    if (!editingPlaylist) return;

    const tracks = getCsvTracks();
    if (tracks.length === 0) {
        showToast("В плейлисте нет треков для экспорта", "error");
        return;
    }

    const safeTitle = (editingPlaylist.title || "playlist")
        .replace(/[\\/:*?"<>|]+/g, "")
        .trim()
        .slice(0, 80) || "playlist";
    const csv = formatPlaylistCsv(editingPlaylist, tracks);
    const utf8Bom = new Uint8Array([0xef, 0xbb, 0xbf]);
    const encodedCsv = new TextEncoder().encode(csv);
    const blob = new Blob([utf8Bom, encodedCsv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = `${safeTitle}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    showToast("CSV-файл скачан");
}

function openPlaylistEditor(playlist) {
    editingPlaylist = playlist;
    removedTrackIds = new Set();

    const modal = ensurePlaylistEditorModal();
    const titleInput = document.getElementById("edit-playlist-title");
    const promptInput = document.getElementById("edit-playlist-prompt");
    titleInput.value = playlist.title || "";
    promptInput.value = playlist.prompt || "";
    renderEditableTracks();

    modal.classList.add("visible");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
    titleInput.focus();
}

function renderEditableTracks() {
    const listEl = document.getElementById("edit-track-list");
    const summaryEl = document.getElementById("edit-track-summary");
    if (!listEl || !summaryEl || !editingPlaylist) return;

    const visibleTracks = (editingPlaylist.tracks || []).filter((track) => !removedTrackIds.has(track.id));
    summaryEl.textContent = `${formatTrackCount(visibleTracks.length)} ${pluralizeRu(visibleTracks.length, "останется", "останется", "останется")} в плейлисте`;

    if (visibleTracks.length === 0) {
        listEl.innerHTML = `<div class="edit-track-empty">Все треки удалены</div>`;
        return;
    }

    listEl.innerHTML = visibleTracks.map((track) => {
        const cover = track.cover || "♪";
        const coverHtml = String(cover).startsWith("http")
            ? `<img class="edit-track-cover-img" src="${escapeHtml(cover)}" alt="">`
            : `<div class="edit-track-cover">${escapeHtml(cover)}</div>`;

        return `
            <div class="edit-track-item">
                ${coverHtml}
                <div class="edit-track-info">
                    <div class="edit-track-title">${escapeHtml(track.title)}</div>
                    <div class="edit-track-artist">${escapeHtml(track.artist)}</div>
                </div>
                <span class="edit-track-duration">${escapeHtml(track.duration || "")}</span>
                <button type="button" class="remove-track-btn" data-track-id="${track.id}" aria-label="Удалить трек">&times;</button>
            </div>
        `;
    }).join("");
}

async function savePlaylistEdits() {
    if (!editingPlaylist) return;

    const titleInput = document.getElementById("edit-playlist-title");
    const saveBtn = document.getElementById("save-playlist-edit");
    const title = titleInput.value.trim();
    if (!title) {
        showToast("Введите название плейлиста", "error");
        return;
    }

    setLoading(saveBtn, true);
    try {
        const res = await fetch(`${API}/playlists/${editingPlaylist.id}`, {
            method: "PATCH",
            headers: authHeaders(),
            body: JSON.stringify({
                title,
                removed_track_ids: Array.from(removedTrackIds),
            }),
        });

        if (res.status === 401) {
            clearAuth();
            window.location.href = "/login";
            return;
        }

        const data = await res.json();
        if (!res.ok) {
            showToast(data.detail || "Ошибка сохранения плейлиста", "error");
            return;
        }

        closePlaylistEditor();
        showToast("Плейлист сохранён");
        await loadProfile();
        await loadPlaylists();
    } catch {
        showToast("Ошибка сети", "error");
    } finally {
        setLoading(saveBtn, false);
    }
}

async function deleteCurrentPlaylist() {
    if (!pendingDeletePlaylist) return;

    const playlistId = pendingDeletePlaylist.id;
    const deleteBtn = document.getElementById("confirm-delete-playlist");
    setLoading(deleteBtn, true);
    try {
        const res = await fetch(`${API}/playlists/${playlistId}`, {
            method: "DELETE",
            headers: authHeaders(),
        });

        if (res.status === 401) {
            clearAuth();
            window.location.href = "/login";
            return;
        }

        const data = await res.json();
        if (!res.ok) {
            showToast(data.detail || "Ошибка удаления плейлиста", "error");
            return;
        }

        closeDeleteConfirm();
        closePlaylistEditor();
        showToast("Плейлист удалён");
        await loadProfile();
        await loadPlaylists();
    } catch {
        showToast("Ошибка сети", "error");
    } finally {
        setLoading(deleteBtn, false);
    }
}

function initPlaylistEditor() {
    if (!document.querySelector(".profile-page")) return;

    const modal = ensurePlaylistEditorModal();
    const deleteConfirmModal = ensureDeleteConfirmModal();
    modal.addEventListener("click", (e) => {
        if (e.target.closest("[data-modal-close]")) {
            closePlaylistEditor();
            return;
        }

        const removeBtn = e.target.closest(".remove-track-btn");
        if (removeBtn) {
            removedTrackIds.add(Number(removeBtn.dataset.trackId));
            renderEditableTracks();
        }
    });

    document.getElementById("save-playlist-edit").addEventListener("click", savePlaylistEdits);
    document.getElementById("delete-playlist").addEventListener("click", openDeleteConfirm);
    document.getElementById("download-playlist-csv").addEventListener("click", downloadPlaylistCsv);
    deleteConfirmModal.addEventListener("click", (e) => {
        if (e.target.closest("[data-delete-cancel]")) {
            closeDeleteConfirm();
        }
    });
    document.getElementById("confirm-delete-playlist").addEventListener("click", deleteCurrentPlaylist);
    document.addEventListener("keydown", (e) => {
        if (e.key !== "Escape") return;
        if (deleteConfirmModal.classList.contains("visible")) {
            closeDeleteConfirm();
            return;
        }
        if (modal.classList.contains("visible")) {
            closePlaylistEditor();
        }
    });
}

function getSortedPlaylists() {
    const collator = new Intl.Collator("ru", {
        numeric: true,
        sensitivity: "base",
    });
    const query = playlistSearchQuery.trim().toLowerCase();
    const searched = query
        ? profilePlaylists.filter((playlist) => (playlist.title || "").toLowerCase().includes(query))
        : profilePlaylists;
    const filtered = playlistFavoritesOnly
        ? searched.filter((playlist) => playlist.is_favorite)
        : searched;

    return [...filtered].sort((a, b) => {
        if (playlistSortMode === "date-old") {
            return new Date(a.created_at) - new Date(b.created_at);
        }
        if (playlistSortMode === "title-asc") {
            return collator.compare(a.title || "", b.title || "");
        }
        if (playlistSortMode === "title-desc") {
            return collator.compare(b.title || "", a.title || "");
        }
        return new Date(b.created_at) - new Date(a.created_at);
    });
}

function updateFavoriteFilterState() {
    const btn = document.getElementById("favorite-filter");
    const countEl = document.getElementById("favorite-count");
    const favoriteCount = profilePlaylists.filter((playlist) => playlist.is_favorite).length;

    if (countEl) countEl.textContent = favoriteCount;
    if (!btn) return;

    btn.classList.toggle("active", playlistFavoritesOnly);
    btn.setAttribute("aria-pressed", playlistFavoritesOnly ? "true" : "false");
    btn.disabled = profilePlaylists.length === 0;
}

function renderPlaylistCoverCollage(playlist) {
    const covers = (playlist.tracks || [])
        .map((track) => track.cover)
        .filter((cover) => typeof cover === "string" && cover.startsWith("http"))
        .slice(0, 4);
    const cells = Array.from({ length: 4 }, (_, index) => {
        const cover = covers[index];
        if (cover) {
            return `<img src="${escapeHtml(cover)}" alt="" loading="lazy">`;
        }
        return `<span>&#9835;</span>`;
    }).join("");

    return `<div class="playlist-cover-collage" aria-hidden="true">${cells}</div>`;
}

function renderPlaylistHistory() {
    const container = document.getElementById("playlists-history");
    if (!container) return;
    updateFavoriteFilterState();

    if (profilePlaylists.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">&#127925;</span>
                <p>Плейлисты пока не созданы</p>
                <a href="/generate" class="btn">Создать первый</a>
            </div>`;
        return;
    }

    const visiblePlaylists = getSortedPlaylists();
    if (visiblePlaylists.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">&#128269;</span>
                <p>Плейлисты не найдены</p>
            </div>`;
        return;
    }

    container.innerHTML = "";
    visiblePlaylists.forEach((pl) => {
        const item = document.createElement("div");
        item.className = `history-item card${pl.is_favorite ? " favorite" : ""}`;
        const d = new Date(pl.created_at);
        item.innerHTML = `
            <div class="history-item-content">
                ${renderPlaylistCoverCollage(pl)}
                <div class="history-item-main">
                    <div class="history-title">${escapeHtml(pl.title)}</div>
                    <div class="history-meta">${d.toLocaleDateString("ru-RU")}</div>
                </div>
            </div>
            <div class="history-item-actions">
                <button type="button" class="playlist-favorite-btn${pl.is_favorite ? " active" : ""}" data-playlist-id="${pl.id}" aria-label="${pl.is_favorite ? "Убрать из избранного" : "Добавить в избранное"}">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M12 3.5 14.7 9l6 .9-4.35 4.22 1.03 5.96L12 17.26l-5.38 2.82 1.03-5.96L3.3 9.9l6-.9L12 3.5Z"></path>
                    </svg>
                    <span class="favorite-spark spark-1"></span>
                    <span class="favorite-spark spark-2"></span>
                    <span class="favorite-spark spark-3"></span>
                </button>
                <span class="history-tracks-count">${formatTrackCount((pl.tracks || []).length)}</span>
            </div>
        `;
        item.addEventListener("click", () => openPlaylistEditor(pl));
        const favoriteBtn = item.querySelector(".playlist-favorite-btn");
        favoriteBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            togglePlaylistFavorite(pl.id, favoriteBtn);
        });
        container.appendChild(item);
    });
}

function initPlaylistSorting() {
    const select = document.getElementById("playlist-sort");
    if (!select) return;

    select.value = playlistSortMode;
    select.addEventListener("change", () => {
        playlistSortMode = select.value;
        localStorage.setItem("playlistSortMode", playlistSortMode);
        renderPlaylistHistory();
    });
}

function initPlaylistSearch() {
    const input = document.getElementById("playlist-search");
    if (!input) return;

    input.addEventListener("input", () => {
        playlistSearchQuery = input.value;
        renderPlaylistHistory();
    });
}

function initFavoriteFilter() {
    const btn = document.getElementById("favorite-filter");
    if (!btn) return;

    btn.addEventListener("click", () => {
        playlistFavoritesOnly = !playlistFavoritesOnly;
        renderPlaylistHistory();
    });
}

function playFavoriteBurst(button) {
    if (!button) return;

    button.classList.remove("favorite-burst");
    void button.offsetWidth;
    requestAnimationFrame(() => {
        button.classList.add("favorite-burst");
    });
}

async function togglePlaylistFavorite(playlistId, triggerButton = null) {
    const playlist = profilePlaylists.find((item) => item.id === playlistId);
    if (!playlist) return;

    const previousValue = Boolean(playlist.is_favorite);
    playlist.is_favorite = !previousValue;
    renderPlaylistHistory();
    if (playlist.is_favorite) {
        const btn = document.querySelector(`.playlist-favorite-btn[data-playlist-id="${playlistId}"]`) || triggerButton;
        playFavoriteBurst(btn);
    }

    try {
        const res = await fetch(`${API}/playlists/${playlistId}/favorite`, {
            method: "PATCH",
            headers: authHeaders(),
            body: JSON.stringify({ is_favorite: playlist.is_favorite }),
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Ошибка сохранения избранного");
        }

        const confirmedValue = Boolean(data.is_favorite);
        if (playlist.is_favorite !== confirmedValue) {
            playlist.is_favorite = confirmedValue;
            renderPlaylistHistory();
        } else {
            updateFavoriteFilterState();
        }
        showToast(playlist.is_favorite ? "Плейлист добавлен в избранное" : "Плейлист убран из избранного");
    } catch (error) {
        playlist.is_favorite = previousValue;
        renderPlaylistHistory();
        showToast(error.message || "Ошибка сохранения избранного", "error");
    }
}

async function loadPlaylists() {
    try {
        const res = await fetch(`${API}/playlists`, { headers: authHeaders() });
        const data = await res.json();

        const playlists = data.playlists || [];
        profilePlaylists = playlists;
        const statTracks = document.getElementById("stat-tracks");

        let totalTracks = 0;
        playlists.forEach((p) => (totalTracks += (p.tracks || []).length));
        if (statTracks) statTracks.textContent = totalTracks;

        renderPlaylistHistory();
    } catch {
        showToast("Ошибка загрузки плейлистов", "error");
    }
}

// ===== ИНИЦИАЛИЗАЦИЯ =====

document.addEventListener("DOMContentLoaded", () => {
    updateNav();
    initPasswordReveal();

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
    initProfileEdit();
    initPlaylistEditor();
    initPlaylistSorting();
    initPlaylistSearch();
    initFavoriteFilter();

    if (document.querySelector(".profile-page")) {
        initProfile();
    }
});
