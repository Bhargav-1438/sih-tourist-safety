/** Minimal application layout: header, navigation, content outlet, footer. */
import { NavLink, Outlet } from "react-router-dom";

export default function AppLayout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="app-title">SIH Tourist Safety</h1>
        <nav className="app-nav">
          <NavLink to="/" end>
            Home
          </NavLink>
          <NavLink to="/tourist">Tourist</NavLink>
          <NavLink to="/authority">Authority</NavLink>
        </nav>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <footer className="app-footer">
        <small>
          Prototype &mdash; synthetic demonstration data only. Not real crime
          statistics.
        </small>
      </footer>
    </div>
  );
}
