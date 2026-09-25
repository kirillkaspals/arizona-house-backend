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
