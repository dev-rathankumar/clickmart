import { Package, ShoppingCart, TrendingUp } from "lucide-react";
import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";

const Dashboard = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const stats = [
    { label: "Total Orders", value: "12", icon: Package, color: "primary" },
    { label: "Cart Items", value: "3", icon: ShoppingCart, color: "success" },
    { label: "Wishlist", value: "8", icon: TrendingUp, color: "warning" },
  ];

  const recentOrders = [
    {
      id: "#ORD-001",
      date: "2024-01-15",
      total: "$129.99",
      status: "Delivered",
    },
    { id: "#ORD-002", date: "2024-01-12", total: "$89.50", status: "Shipped" },
    {
      id: "#ORD-003",
      date: "2024-01-08",
      total: "$199.99",
      status: "Processing",
    },
  ];

  const getStatusBadge = (status) => {
    const statusClasses = {
      Delivered: "bg-success",
      Shipped: "bg-info",
      Processing: "bg-warning",
      Pending: "bg-secondary",
    };
    return statusClasses[status] || "bg-secondary";
  };

  return (
    <div className="d-flex">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-grow-1 main-content">
        <div className="bg-white shadow-sm p-3 mb-4">
          <div className="d-flex justify-content-between align-items-center">
            <div className="d-flex align-items-center">
              <h4 className="mb-0 fw-bold">Dashboard</h4>
            </div>
          </div>
        </div>
        <Outlet />
      </div>
    </div>
  );
};

export default Dashboard;
