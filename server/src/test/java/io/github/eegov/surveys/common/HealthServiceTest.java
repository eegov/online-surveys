package io.github.eegov.surveys.common;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.dao.DataAccessResourceFailureException;
import org.springframework.jdbc.core.JdbcTemplate;

@ExtendWith(MockitoExtension.class)
class HealthServiceTest {

    @Mock
    private JdbcTemplate jdbcTemplate;

    @InjectMocks
    private HealthService healthService;

    @Test
    void returnsUpWithDatabaseVersion() {
        when(jdbcTemplate.queryForObject(anyString(), eq(String.class))).thenReturn("PostgreSQL 18.1");

        HealthStatus status = healthService.check();

        assertThat(status.isUp()).isTrue();
        assertThat(status.database()).isEqualTo("PostgreSQL 18.1");
    }

    @Test
    void returnsDownWhenDatabaseFails() {
        when(jdbcTemplate.queryForObject(anyString(), eq(String.class)))
                .thenThrow(new DataAccessResourceFailureException("connection refused"));

        HealthStatus status = healthService.check();

        assertThat(status.isUp()).isFalse();
        assertThat(status.database()).isEqualTo("unavailable");
    }

    @Test
    void returnsDownWhenVersionIsEmpty() {
        when(jdbcTemplate.queryForObject(anyString(), eq(String.class))).thenReturn(" ");

        HealthStatus status = healthService.check();

        assertThat(status.isUp()).isFalse();
    }
}
