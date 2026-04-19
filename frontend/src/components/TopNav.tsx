import { NavLink } from 'react-router-dom';

export default function TopNav() {
  return (
    <nav className="top-nav">
      <NavLink to="/" className="nav-logo">
        <span className="nav-logo-dot" />
        SkillRoute
      </NavLink>

      <div className="nav-links">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/active-tickets"
          className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
        >
          Active Tickets
        </NavLink>
        <NavLink
          to="/bottlenecks"
          className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
        >
          Bottlenecks
        </NavLink>
      </div>

      <div className="nav-right">
        <span className="nav-status-dot" />
        <span className="nav-status-text">AI Engine Online</span>
      </div>
    </nav>
  );
}
