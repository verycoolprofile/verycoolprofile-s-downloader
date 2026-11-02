// Переводы (RU / ENG)
const TR = {
    ru: {
        title: "verycoolprofile's downloader",
        subtitle: "Скачивай видео и аудио с YouTube",
        audio: "Аудио (MP3)",
        video: "Видео (MP4)",
        quality: "Качество",
        download: "Скачать",
        connecting: "Подключение к серверу...",
        success: "Готово! Файл отправлен на скачивание",
        error: "Ошибка соединения с сервером!",
        error_tab: "Ошибка: не удалось получить URL вкладки",
        theme: "Тема",
        lang: "RU",
        idle: ""
    },
    en: {
        title: "verycoolprofile's downloader",
        subtitle: "Download video and audio from YouTube",
        audio: "Audio (MP3)",
        video: "Video (MP4)",
        quality: "Quality",
        download: "Download",
        connecting: "Connecting to server...",
        success: "Done! File sent for download",
        error: "Server connection error!",
        error_tab: "Error: could not get tab URL",
        theme: "Theme",
        lang: "ENG",
        idle: ""
    }
};

// Наборы качества по языкам
const QUALITY_OPTIONS = {
    ru: {
        mp3: [
            { label: "128 kbps (Низкое)", value: "128" },
            { label: "192 kbps (Среднее)", value: "192", selected: true },
            { label: "256 kbps (Хорошее)", value: "256" },
            { label: "320 kbps (Максимальное)", value: "320" }
        ],
        mp4: [
            { label: "360p", value: "360" },
            { label: "480p", value: "480" },
            { label: "720p (HD)", value: "720", selected: true },
            { label: "1080p (Full HD)", value: "1080" },
            { label: "1440p (2K)", value: "1440" },
            { label: "2160p (4K)", value: "2160" },
            { label: "Best Available", value: "best" }
        ]
    },
    en: {
        mp3: [
            { label: "128 kbps (Low)", value: "128" },
            { label: "192 kbps (Medium)", value: "192", selected: true },
            { label: "256 kbps (Good)", value: "256" },
            { label: "320 kbps (Maximum)", value: "320" }
        ],
        mp4: [
            { label: "360p", value: "360" },
            { label: "480p", value: "480" },
            { label: "720p (HD)", value: "720", selected: true },
            { label: "1080p (Full HD)", value: "1080" },
            { label: "1440p (2K)", value: "1440" },
            { label: "2160p (4K)", value: "2160" },
            { label: "Best Available", value: "best" }
        ]
    }
};

let currentLang = localStorage.getItem('downloader_lang') || 'ru';
let currentTheme = localStorage.getItem('downloader_theme') || 'youtube';

document.addEventListener('DOMContentLoaded', () => {
    const formatRadios = document.querySelectorAll('input[name="format"]');
    const btnDownload = document.getElementById('btnDownload');
    const btnTheme = document.getElementById('btnTheme');
    const btnLang = document.getElementById('btnLang');

    // Применяем сохранённые настройки
    applyTheme(currentTheme);
    applyLang(currentLang);

    // Обновляем список качества при старте
    const selectedFormat = document.querySelector('input[name="format"]:checked').value;
    updateQualityOptions(selectedFormat);

    // Переключение формата (MP3 / MP4)
    formatRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            document.querySelectorAll('.toggle').forEach(lbl => lbl.classList.remove('active'));
            e.target.closest('.toggle').classList.add('active');
            updateQualityOptions(e.target.value);
        });
    });

    // Кнопка темы: цикл youtube → dark → light → youtube
    btnTheme.addEventListener('click', () => {
        const order = ['youtube', 'dark', 'light'];
        const idx = order.indexOf(currentTheme);
        const next = order[(idx + 1) % order.length];
        applyTheme(next);
    });

    // Кнопка языка: RU ↔ ENG
    btnLang.addEventListener('click', () => {
        applyLang(currentLang === 'ru' ? 'en' : 'ru');
    });

    // Кнопка скачивания
    btnDownload.addEventListener('click', handleDownload);
});

function applyTheme(theme) {
    currentTheme = theme;
    localStorage.setItem('downloader_theme', theme);
    document.documentElement.setAttribute('data-theme', theme);

    const btnTheme = document.getElementById('btnTheme');
    if (btnTheme) {
        btnTheme.title = TR[currentLang].theme;
        const labels = { youtube: 'YouTube', dark: 'Dark', light: 'Light' };
        btnTheme.setAttribute('aria-label', `${TR[currentLang].theme} (${labels[theme]})`);
    }
}

function applyLang(lang) {
    currentLang = lang;
    localStorage.setItem('downloader_lang', lang);

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (TR[lang] && TR[lang][key] !== undefined) {
            el.textContent = TR[lang][key];
        }
    });

    const btnLang = document.getElementById('btnLang');
    if (btnLang) btnLang.textContent = lang === 'ru' ? 'RU' : 'ENG';

    document.documentElement.lang = lang;

    // Перерисовать качество с учётом текущего языка
    const selectedFormat = document.querySelector('input[name="format"]:checked')?.value || 'mp3';
    updateQualityOptions(selectedFormat);
}

function updateQualityOptions(format) {
    const qualitySelect = document.getElementById('quality');
    qualitySelect.innerHTML = '';

    const options = (QUALITY_OPTIONS[currentLang] && QUALITY_OPTIONS[currentLang][format]) || [];
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.label;
        if (opt.selected) option.selected = true;
        qualitySelect.appendChild(option);
    });
}

function setLoading(isLoading) {
    const btn = document.getElementById('btnDownload');
    const status = document.getElementById('status');

    if (isLoading) {
        btn.classList.add('loading');
        btn.disabled = true;
        status.textContent = TR[currentLang].connecting;
        status.className = "info";
    } else {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

function showStatus(message, type) {
    const status = document.getElementById('status');
    status.textContent = message;
    status.className = type || "info";
}

async function handleDownload() {
    const selectedFormat = document.querySelector('input[name="format"]:checked').value;
    const quality = document.getElementById('quality').value;

    setLoading(true);

    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab || !tab.url) {
            showStatus(TR[currentLang].error_tab, "error");
            return;
        }

        const response = await fetch('http://127.0.0.1:5000/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: tab.url,
                type: selectedFormat,
                quality: quality
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();
        showStatus(TR[currentLang].success, "success");
    } catch (err) {
        console.error(err);
        showStatus(TR[currentLang].error, "error");
    } finally {
        setLoading(false);
    }
}