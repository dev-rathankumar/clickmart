import { Home, Package, ShoppingCart, User } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const Sidebar = ({ isOpen, onClose }) => {
  const location = useLocation();

  const menuItems = [
    { path: "/dashboard", icon: Home, label: "Dashboard" },
    { path: "orders", icon: Package, label: "My Orders" },
    { path: "profile", icon: User, label: "Profile" },
  ];

  return (
    <>
      {isOpen && (
        <div
          className="d-md-none"
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            zIndex: 999,
          }}
          onClick={onClose}
        ></div>
      )}

      <div className={`sidebar ${isOpen ? "show" : ""}`}>
        <div className="p-4">
          <h5 className="text-white mb-4">Menu</h5>
          <nav className="nav flex-column">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`nav-link ${isActive ? "active" : ""}`}
                  onClick={onClose}
                >
                  <Icon size={18} className="me-3" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
