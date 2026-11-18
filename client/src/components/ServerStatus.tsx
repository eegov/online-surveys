import { useEffect, useState } from 'react';
import { fetchHealth, type HealthStatus } from '../api/health';

type State =
  | { kind: 'loading' }
  | { kind: 'loaded'; health: HealthStatus }
  | { kind: 'error'; message: string };

/** Показывает, отвечает ли сервер и видит ли он базу данных. */
export function ServerStatus() {
  const [state, setState] = useState<State>({ kind: 'loading' });

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then((health) => !cancelled && setState({ kind: 'loaded', health }))
      .catch((e: Error) => !cancelled && setState({ kind: 'error', message: e.message }));
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.kind === 'loading') {
    return <p className="status">Проверяем сервер…</p>;
  }
  if (state.kind === 'error') {
    return <p className="status status-down">Сервер недоступен: {state.message}</p>;
  }
  const { health } = state;
  return health.status === 'UP' ? (
    <p className="status status-up">Сервер работает, база данных: {health.database}</p>
  ) : (
    <p className="status status-down">Сервер работает, база данных недоступна</p>
  );
}
