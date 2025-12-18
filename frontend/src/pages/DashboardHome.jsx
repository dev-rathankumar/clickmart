import { Package, ShoppingCart, TrendingUp, User } from "lucide-react";

import { Link } from "react-router-dom";

const DashboardHome = () => {
  const stats = [
    { label: "Total Orders", value: "12", icon: Package, color: "primary" },
    { label: "Cart Items", value: "3", icon: ShoppingCart, color: "success" },
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
    <>
      <div className="container-fluid ">
        {/* Welcome Card */}
        <div className="row mb-4">
          <div className="col-12">
            <div className="card dashboard-card">
              <div className="card-body">
                <h2 className="card-title mb-2">Welcome back, user name! 👋</h2>
                <p className="card-text mb-0 opacity-75">
                  Here's what's happening with your account today.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="row mb-4">
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div key={index} className="col-md-6 mb-3">
                <div className="card">
                  <div className="card-body">
                    <div className="d-flex justify-content-between align-items-center">
                      <div>
                        <h3 className="card-title h2 mb-1">{stat.value}</h3>
                        <p className="card-text text-muted mb-0">
                          {stat.label}
                        </p>
                      </div>
                      <div className={`text-${stat.color}`}>
                        <Icon size={32} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="row">
          {/* Recent Orders */}
          <div className="col-lg-12 mb-4">
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h5 className="card-title mb-0">Recent Orders</h5>
                <Link to="/orders" className="btn btn-outline-primary btn-sm">
                  View All
                </Link>
              </div>
              <div className="card-body">
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Order ID</th>
                        <th>Date</th>
                        <th>Total</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recentOrders.map((order) => (
                        <tr key={order.id}>
                          <td className="fw-semibold">{order.id}</td>
                          <td>{order.date}</td>
                          <td className="fw-semibold">{order.total}</td>
                          <td>
                            <span
                              className={`badge order-status-badge ${getStatusBadge(
                                order.status
                              )}`}
                            >
                              {order.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </>
  );
};

export default DashboardHome;
