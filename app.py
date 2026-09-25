const express = require('express');
const app = express();

app.use(express.json());
app.use(express.static('public'));
app.set('view engine', 'ejs');

// Пример базы данных в памяти (или замените на вашу MongoDB/PostgreSQL)
let propertyData = {}; 

// Эндпоинт приёма данных от Lua-скрипта
app.post('/update', (req, res) => {
    const { server, entries } = req.body;
    if (!server || !entries) {
        return res.status(400).json({ error: 'Invalid data' });
    }

    // Разделяем входящие объекты на дома и бизнесы
    propertyData[server] = {
        houses: entries.filter(e => e.propType === 'house'),
        businesses: entries.filter(e => e.propType === 'business'),
        updatedAt: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    };

    res.json({ status: 'ok' });
});

// Главная страница
app.get('/', (req, res) => {
    res.render('index', { data: propertyData });
});

app.listen(3000, () => console.log('Server started on port 3000'));
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arizona RP — Мониторинг слетов</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f1117;
            --card-bg: #181b23;
            --border-color: #272b36;
            --accent-green: #22c55e;
            --accent-blue: #3b82f6;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }

        .container {
            width: 100%;
            max-width: 800px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 10px;
        }

        .header h1 {
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 8px 0;
        }

        .header p {
            color: var(--text-muted);
            margin: 0;
            font-size: 14px;
        }

        /* Карточка сервера */
        .server-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }

        .server-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
            margin-bottom: 16px;
        }

        .server-title {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .server-time {
            font-size: 12px;
            color: var(--text-muted);
            background: #212530;
            padding: 4px 8px;
            border-radius: 6px;
        }

        /* Сетки для категорий */
        .categories-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        @media (max-width: 600px) {
            .categories-grid {
                grid-template-columns: 1fr;
            }
        }

        .category-box {
            background-color: #12141a;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
        }

        .category-title {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
        }

        .category-title.house { color: var(--accent-green); }
        .category-title.business { color: var(--accent-blue); }

        /* Список объектов */
        .property-list {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .property-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #181b23;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 13px;
        }

        .property-id {
            font-weight: 500;
        }

        .property-pd {
            font-weight: 600;
            color: #ef4444;
            background: rgba(239, 68, 68, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
        }

        .empty-text {
            color: var(--text-muted);
            font-size: 13px;
            text-align: center;
            margin: 10px 0;
        }
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1>Arizona RP — Мониторинг недвижимости</h1>
        <p>Автоматическое обновление данных с серверов</p>
    </div>

    <% 
      const serverList = ["Saint-Rose", "Phoenix", "Tucson", "Scottdale", "Chandler", "Mesa"]; 
      serverList.forEach(serverName => { 
        const server = data[serverName];
    %>
        <!-- Карточка Сервера -->
        <div class="server-card">
            <div class="server-header">
                <div class="server-title">
                    🌐 Сервер: <%= serverName %>
                </div>
                <% if (server) { %>
                    <div class="server-time">Обновлено: <%= server.updatedAt %></div>
                <% } %>
            </div>

            <% if (server && (server.houses.length > 0 || server.businesses.length > 0)) { %>
                <div class="categories-grid">
                    
                    <!-- Дома -->
                    <div class="category-box">
                        <div class="category-title house">
                            <span>🏠 Дома</span>
                            <span>(<%= server.houses.length %>)</span>
                        </div>
                        <% if (server.houses.length > 0) { %>
                            <ul class="property-list">
                                <% server.houses.forEach((item, index) => { %>
                                    <li class="property-item">
                                        <span class="property-id">
                                            <%= item.propId ? 'Дом №' + item.propId : (index + 1) + '. Дом' %>
                                        </span>
                                        <span class="property-pd"><%= item.pd %> PD</span>
                                    </li>
                                <% }); %>
                            </ul>
                        <% } else { %>
                            <div class="empty-text">Нет домов</div>
                        <% } %>
                    </div>

                    <!-- Бизнесы -->
                    <div class="category-box">
                        <div class="category-title business">
                            <span>💼 Бизнесы</span>
                            <span>(<%= server.businesses.length %>)</span>
                        </div>
                        <% if (server.businesses.length > 0) { %>
                            <ul class="property-list">
                                <% server.businesses.forEach((item, index) => { %>
                                    <li class="property-item">
                                        <span class="property-id">
                                            <%= item.propId ? 'Бизнес №' + item.propId : (index + 1) + '. Бизнес' %>
                                        </span>
                                        <span class="property-pd"><%= item.pd %> PD</span>
                                    </li>
                                <% }); %>
                            </ul>
                        <% } else { %>
                            <div class="empty-text">Нет бизнесов</div>
                        <% } %>
                    </div>

                </div>
            <% } else { %>
                <div class="empty-text">Нет данных по серверу <%= serverName %></div>
            <% } %>
        </div>
    <% }); %>

</div>

</body>
</html>
