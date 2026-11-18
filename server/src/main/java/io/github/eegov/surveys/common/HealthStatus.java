package io.github.eegov.surveys.common;

/**
 * Состояние сервера для сквозной проверки связи клиента, сервера и базы данных.
 *
 * @param status   UP, если база данных ответила, иначе DOWN
 * @param database версия СУБД или причина недоступности
 */
public record HealthStatus(String status, String database) {

    public static final String UP = "UP";
    public static final String DOWN = "DOWN";

    public boolean isUp() {
        return UP.equals(status);
    }
}
