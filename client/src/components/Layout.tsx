import { NavLink, Outlet } from 'react-router';

const sections = [
  { to: '/', label: 'Главная' },
  { to: '/surveys', label: 'Мои опросы' },
  { to: '/login', label: 'Вход' },
];

export function Layout() {
  return (
    <div className="layout">
      <header className="header">
        <span className="logo">Опросы</span>
        <nav className="nav">
          {sections.map((s) => (
            <NavLink key={s.to} to={s.to} end>
              {s.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
