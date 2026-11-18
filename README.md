# Онлайн-опросы

Web-приложение для создания и проведения онлайн-опросов: автор создаёт опрос, публикует его по ссылке
и смотрит результаты, респондент проходит опрос по ссылке.

## Структура

| Папка | Содержимое |
|---|---|
| `server/` | сервер: Java 21, Spring Boot 3, PostgreSQL, Flyway, сборка Maven |
| `client/` | клиент: React, TypeScript, Vite, React Router |
| `scripts/` | скрипт сбора метрик качества |
| `.github/workflows/` | пайплайны CI, проверки PR, релиз |
| `compose.yaml` | PostgreSQL для локальной разработки |

## Запуск для разработки

Нужны JDK 21, Node.js 24 и Docker.

```bash
npm install                 # hook проверки сообщений коммитов
docker compose up -d        # PostgreSQL на localhost:5432
cd server && ./mvnw spring-boot:run      # сервер на http://localhost:8080
cd client && npm install && npm run dev  # клиент на http://localhost:5173
```

Проверка связи клиента, сервера и базы данных: на главной странице клиента выводится версия PostgreSQL,
которую сервер прочитал из базы (`GET /api/health`).

## Проверки

```bash
cd server && ./mvnw checkstyle:check verify   # линтер, модульные и интеграционные тесты, покрытие
cd client && npm run lint && npm run format:check && npm test && npm run build
```

Интеграционные тесты сервера запускают PostgreSQL в Docker через Testcontainers, поэтому Docker должен работать.

## Порядок работы

Правила коммитов, ветвления, слияния, релизов и состав метрик описаны в [CONTRIBUTING.md](CONTRIBUTING.md).
