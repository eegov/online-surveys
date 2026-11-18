import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ServerStatus } from './ServerStatus';

function mockFetch(status: number, body: unknown) {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }),
  );
}

describe('ServerStatus', () => {
  it('показывает версию базы, если сервер ответил UP', async () => {
    mockFetch(200, { status: 'UP', database: 'PostgreSQL 18.1' });
    render(<ServerStatus />);
    expect(await screen.findByText(/PostgreSQL 18\.1/)).toBeInTheDocument();
  });

  it('сообщает о недоступной базе при ответе 503', async () => {
    mockFetch(503, { status: 'DOWN', database: 'unavailable' });
    render(<ServerStatus />);
    expect(await screen.findByText(/база данных недоступна/)).toBeInTheDocument();
  });

  it('сообщает об ошибке сервера', async () => {
    mockFetch(500, {});
    render(<ServerStatus />);
    expect(await screen.findByText(/Сервер недоступен: HTTP 500/)).toBeInTheDocument();
  });
});
