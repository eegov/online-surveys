package io.github.eegov.surveys.common;

import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

/**
 * Проверяет, что сервер достаёт данные из базы: читает версию PostgreSQL.
 */
@Service
public class HealthService {

    private final JdbcTemplate jdbcTemplate;

    public HealthService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public HealthStatus check() {
        try {
            String version = jdbcTemplate.queryForObject("select version()", String.class);
            if (version == null || version.isBlank()) {
                return new HealthStatus(HealthStatus.DOWN, "empty response");
            }
            return new HealthStatus(HealthStatus.UP, version);
        } catch (DataAccessException e) {
            return new HealthStatus(HealthStatus.DOWN, "unavailable");
        }
    }
}
