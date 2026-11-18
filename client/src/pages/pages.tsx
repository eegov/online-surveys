import { ServerStatus } from '../components/ServerStatus';

export function HomePage() {
  return (
    <section>
      <h1>Онлайн-опросы</h1>
      <p>Создавайте опросы, публикуйте их по ссылке и смотрите результаты.</p>
      <ServerStatus />
    </section>
  );
}

export function SurveysPage() {
  return (
    <section>
      <h1>Мои опросы</h1>
      <p>Список опросов появится на этапе «Конструктор опросов».</p>
    </section>
  );
}

export function LoginPage() {
  return (
    <section>
      <h1>Вход</h1>
      <p>Регистрация и вход появятся на этапе «Инфраструктура».</p>
    </section>
  );
}

export function NotFoundPage() {
  return (
    <section>
      <h1>Страница не найдена</h1>
    </section>
  );
}
