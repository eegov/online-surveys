import { Route, Routes } from 'react-router';
import { Layout } from './components/Layout';
import { HomePage, LoginPage, NotFoundPage, SurveysPage } from './pages/pages';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="surveys" element={<SurveysPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
