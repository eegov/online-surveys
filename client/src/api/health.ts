export interface HealthStatus {
  status: 'UP' | 'DOWN';
  database: string;
}

/** Запрашивает состояние сервера. Ответ 503 тоже содержит тело со статусом DOWN. */
export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch('/api/health');
  if (!response.ok && response.status !== 503) {
    throw new Error(`HTTP ${response.status}`);
  }
  return (await response.json()) as HealthStatus;
}
