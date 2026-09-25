const express = require('express');
const app = express();

const PORT = process.env.PORT || 3000;
const SECRET_KEY = "usefguIHSFUSDFGUjhjfk88448";

// Хранилище данных в памяти сервера
let propertyData = {};

app.use(express.json({ limit: '1mb' }));

// Middleware для проверки секретного ключа Lua-скрипта
const authCheck = (req, res, next) => {
    const key = req.headers['x-secret-key'];
    if (key !== SECRET_KEY) {
        return res.status(403).json({ error: 'Forbidden: Invalid Secret Key' });
    }
    next();
};

// Эндпоинт приема данных от Lua-скрипта из игры
app.post('/update', authCheck, (req, res) => {
    const { server, scanner, entries } = req.body;

    if (!server || !Array.isArray(entries)) {
        return res.status(400).json({ error: 'Bad Request: Missing server or entries' });
    }

    const houses = entries.filter(e => e.propType === 'house');
    const businesses = entries.filter(e => e.propType === 'business');

    propertyData[server] = {
        houses,
        businesses,
        scanner: scanner || 'Аноним',
        updatedAt: new Date().toLocaleTimeString('ru-RU', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit',
            timeZone: 'Europe/Moscow' 
        })
    };

    console.log(`[${new Date().toLocaleTimeString()}] Обновлен сервер ${server}: ${houses.length} домов, ${businesses.length} бизнесов (от ${scanner})`);
    res.json({ status: 'ok', message: 'Data received' });
});

// Эндпоинт получения времени (для синхронизации Lua)
app.get('/time', (req, res) => {
    res.json({ time: Math.floor(Date.now() / 1000) });
});

// Главная страница веб-интерфейса
app.get('/', (req, res) => {
    const allServers = [
        "Phoenix", "Tucson", "Scottdale", "Chandler", "Brainburg", "Saint-Rose",
        "Mesa", "Red-Rock", "Yuma", "Surprise", "Prescott", "Glendale",
        "Kingman", "Winslow", "Payson", "Gilbert", "Show Low", "Casa-Grande",
        "Page", "Sun-City", "Queen-Creek", "Sedona", "Holiday", "Wednesday",
        "Yava", "Faraway", "Bumble Bee", "Christmas", "Love", "Mirage", "Drake", "Space"
    ];

    const html = `
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Arizona RP — Мониторинг слетов</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-color: #0b0c10;
                --card-bg: #14161d;
                --box-bg: #1c1f2b;
                --border-color: #2a2e3d;
                --accent-green: #22c55e;
                --accent-blue: #3b82f6;
                --text-main: #f3f4f6;
                --text-muted: #8c93a4;
                --pd-bg: rgba(239, 68, 68, 0.12);
                --pd-color: #f87171;
            }

            * { box-sizing: border-box; }

            body {
                font-family: 'Inter', sans-serif;
                background-color: var(--bg-color);
                color: var(--text-main);
                margin: 0;
                padding: 30px 15px;
                display: flex;
                justify-content: center;
            }

            .container {
                width: 100%;
                max-width: 850px;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }

            .header {
                text-align: center;
                margin-bottom: 10px;
            }

            .header h1 {
                font-size: 26px;
                font-weight: 700;
                margin: 0 0 8px 0;
                letter-spacing: -0.5px;
            }

            .header p {
                color: var(--text-muted);
                margin: 0;
                font-size: 14px;
            }

            .server-card {
                background-color: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 20px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            }

            .server-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 14px;
                margin-bottom: 16px;
            }

            .server-title {
                font-size: 18px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .server-meta {
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .server-time {
                font-size: 12px;
                color: var(--text-muted);
                background: #1c1f2b;
                padding: 5px 10px;
                border-radius: 6px;
                border: 1px solid var(--border-color);
            }

            .categories-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
            }

            @media (max-width: 640px) {
                .categories-grid { grid-template-columns: 1fr; }
            }

            .category-box {
                background-color: var(--box-bg);
                border: 1px solid var(--border-color);
                border-radius: 10px;
                padding: 14px;
            }

            .category-title {
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .category-title.house { color: var(--accent-green); }
            .category-title.business { color: var(--accent-blue); }

            .property-list {
                list-style: none;
                padding: 0;
                margin: 0;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .property-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: var(--card-bg);
                padding: 10px 14px;
                border-radius: 8px;
                font-size: 14px;
                border: 1px solid rgba(255, 255, 255, 0.03);
            }

            .property-id { font-weight: 500; }

            .property-pd {
                font-weight: 600;
                color: var(--pd-color);
                background: var(--pd-bg);
                padding: 3px 8px;
                border-radius: 5px;
                font-size: 13px;
            }

            .empty-text {
                color: var(--text-muted);
                font-size: 13px;
                text-align: center;
                padding: 12px 0;
            }
        </style>
        <script>
            // Автоматическое обновление страницы каждые 15 секунд
            setInterval(() => { location.reload(); }, 15000);
        </script>
    </head>
    <body>

    <div class="container">
        <div class="header">
            <h1>Arizona RP — Мониторинг Слетов</h1>
            <p>Списки слетающих домов и бизнесов по серверам</p>
        </div>

        ${allServers.map(serverName => {
            const data = propertyData[serverName];
            const hasHouses = data && data.houses && data.houses.length > 0;
            const hasBusinesses = data && data.businesses && data.businesses.length > 0;
            const hasData = hasHouses || hasBusinesses;

            return `
            <div class="server-card">
                <div class="server-header">
                    <div class="server-title">
                        🌐 Сервер: ${serverName}
                    </div>
                    ${data ? `<div class="server-meta"><span class="server-time">Обновлено: ${data.updatedAt} MSK</span></div>` : ''}
                </div>

                ${hasData ? `
                    <div class="categories-grid">
                        <!-- Дома -->
                        <div class="category-box">
                            <div class="category-title house">
                                <span>🏠 Дома</span>
                                <span>(${data.houses.length})</span>
                            </div>
                            ${hasHouses ? `
                                <ul class="property-list">
                                    ${data.houses.map((item, idx) => `
                                        <li class="property-item">
                                            <span class="property-id">${item.propId ? 'Дом №' + item.propId : (idx + 1) + '. Дом'}</span>
                                            <span class="property-pd">${item.pd} PayDay</span>
                                        </li>
                                    `).join('')}
                                </ul>
                            ` : '<div class="empty-text">Нет домов</div>'}
                        </div>

                        <!-- Бизнесы -->
                        <div class="category-box">
                            <div class="category-title business">
                                <span>💼 Бизнесы</span>
                                <span>(${data.businesses.length})</span>
                            </div>
                            ${hasBusinesses ? `
                                <ul class="property-list">
                                    ${data.businesses.map((item, idx) => `
                                        <li class="property-item">
                                            <span class="property-id">${item.propId ? 'Бизнес №' + item.propId : (idx + 1) + '. Бизнес'}</span>
                                            <span class="property-pd">${item.pd} PayDay</span>
                                        </li>
                                    `).join('')}
                                </ul>
                            ` : '<div class="empty-text">Нет бизнесов</div>'}
                        </div>
                    </div>
                ` : `<div class="empty-text">Нет актуальных данных по серверу ${serverName}</div>`}
            </div>
            `;
        }).join('')}
    </div>

    </body>
    </html>
    `;

    res.send(html);
});

app.listen(PORT, () => {
    console.log(`[Server] Запущен и принимает запросы на порту ${PORT}`);
});
