/** Minimal application layout: header, navigation, content outlet, footer. */
import { NavLink, Outlet } from "react-router-dom";

export default function AppLayout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-title-group">
          <h1 className="app-title">
            <span className="app-title-mark" aria-hidden="true" />
            SIH Tourist Safety
          </h1>
          <span className="app-tagline">
            Predictive risk clustering &amp; patrol optimization
          </span>
        </div>
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
