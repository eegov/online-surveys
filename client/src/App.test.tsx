import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe('навигация по разделам', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: 'UP', database: 'PostgreSQL' }), { status: 200 }),
    );
  });

  it('показывает меню со всеми разделами', () => {
    renderAt('/');
    for (const label of ['Главная', 'Мои опросы', 'Вход']) {
      expect(screen.getByRole('link', { name: label })).toBeInTheDocument();
    }
  });

  it.each([
    ['/', 'Онлайн-опросы'],
    ['/surveys', 'Мои опросы'],
    ['/login', 'Вход'],
    ['/unknown', 'Страница не найдена'],
  ])('по адресу %s открывает раздел «%s»', (path, heading) => {
    renderAt(path);
    expect(screen.getByRole('heading', { level: 1, name: heading })).toBeInTheDocument();
  });
});
