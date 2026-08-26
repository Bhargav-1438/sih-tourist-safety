/** Application route table (Prompt 8 scope: foundation placeholders only). */
import { Route, Routes } from "react-router-dom";
import AppLayout from "../components/layout/AppLayout";
import AuthorityPage from "../pages/AuthorityPage";
import HomePage from "../pages/HomePage";
import NotFoundPage from "../pages/NotFoundPage";
import TouristPage from "../pages/TouristPage";

export default function AppRouter() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path="/tourist" element={<TouristPage />} />
        <Route path="/authority" element={<AuthorityPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
