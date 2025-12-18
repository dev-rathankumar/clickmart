import React, { useState, useEffect } from 'react';
import { Package, Eye, Download, Filter } from 'lucide-react';


const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    // Simulate API call
    const fetchOrders = async () => {
      setLoading(true);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockOrders = [
        {
          id: 'ORD-001',
          date: '2024-01-15',
          total: '$129.99',
          status: 'Delivered',
          items: 2,
          trackingNumber: 'TRK123456789'
        },
        {
          id: 'ORD-002',
          date: '2024-01-12',
          total: '$89.50',
          status: 'Shipped',
          items: 1,
          trackingNumber: 'TRK123456790'
        },
        {
          id: 'ORD-003',
          date: '2024-01-08',
          total: '$199.99',
          status: 'Paid',
          items: 3
        },
        {
          id: 'ORD-004',
          date: '2024-01-05',
          total: '$59.99',
          status: 'Pending',
          items: 1
        },
        {
          id: 'ORD-005',
          date: '2024-01-01',
          total: '$299.99',
          status: 'Delivered',
          items: 4,
          trackingNumber: 'TRK123456791'
        }
      ];
      
      setOrders(mockOrders);
      setLoading(false);
    };

    fetchOrders();
  }, []);

  const getStatusBadge = (status) => {
    const statusConfig = {
      'Pending': { class: 'bg-warning text-dark' },
      'Paid': { class: 'bg-info' },
      'Shipped': { class: 'bg-primary' },
      'Delivered': { class: 'bg-success' },
      'Cancelled': { class: 'bg-danger'}
    };
    
    const config = statusConfig[status] || statusConfig['Pending'];
    
    return (
      <span className={`badge order-status-badge ${config.class}`}>
        {status}
      </span>
    );
  };

  const filteredOrders = filter === 'all' 
    ? orders 
    : orders.filter(order => order.status.toLowerCase() === filter);

  if (loading) {
    return (
      <div className="container mt-4">
        <div>Loadin..</div>
      </div>
    );
  }

  return (
    <div className="container mt-4">
      <div className="row">
        <div className="col-12">
          {/* Header */}
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h2 className="mb-1">My Orders</h2>
              <p className="text-muted mb-0">Track and manage your orders</p>
            </div>
            <div className="d-flex gap-2">
              <div className="dropdown">
                <button 
                  className="btn btn-outline-secondary dropdown-toggle"
                  data-bs-toggle="dropdown"
                >
                  <Filter size={18} className="me-2" />
                  Filter
                </button>
                <ul className="dropdown-menu">
                  <li>
                    <button 
                      className="dropdown-item" 
                      onClick={() => setFilter('all')}
                    >
                      All Orders
                    </button>
                  </li>
                  <li>
                    <button 
                      className="dropdown-item" 
                      onClick={() => setFilter('pending')}
                    >
                      Pending
                    </button>
                  </li>
                  <li>
                    <button 
                      className="dropdown-item" 
                      onClick={() => setFilter('shipped')}
                    >
                      Shipped
                    </button>
                  </li>
                  <li>
                    <button 
                      className="dropdown-item" 
                      onClick={() => setFilter('delivered')}
                    >
                      Delivered
                    </button>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Orders Summary Cards */}
          <div className="row mb-4">
            <div className="col-md-3 mb-3">
              <div className="card text-center">
                <div className="card-body">
                  <h4 className="text-primary">{orders.length}</h4>
                  <p className="mb-0 text-muted">Total Orders</p>
                </div>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="card text-center">
                <div className="card-body">
                  <h4 className="text-success">
                    {orders.filter(o => o.status === 'Delivered').length}
                  </h4>
                  <p className="mb-0 text-muted">Delivered</p>
                </div>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="card text-center">
                <div className="card-body">
                  <h4 className="text-info">
                    {orders.filter(o => o.status === 'Shipped').length}
                  </h4>
                  <p className="mb-0 text-muted">In Transit</p>
                </div>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="card text-center">
                <div className="card-body">
                  <h4 className="text-warning">
                    {orders.filter(o => o.status === 'Pending').length}
                  </h4>
                  <p className="mb-0 text-muted">Pending</p>
                </div>
              </div>
            </div>
          </div>

          {/* Orders Table */}
          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">
                <Package size={20} className="me-2" />
                Order History
              </h5>
            </div>
            <div className="card-body">
              {filteredOrders.length === 0 ? (
                <div className="text-center py-5">
                  <Package size={48} className="text-muted mb-3" />
                  <h5>No orders found</h5>
                  <p className="text-muted">
                    {filter === 'all' 
                      ? "You haven't placed any orders yet."
                      : `No ${filter} orders found.`
                    }
                  </p>
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Order ID</th>
                        <th>Date</th>
                        <th>Items</th>
                        <th>Total</th>
                        <th>Status</th>
                        <th>Tracking</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredOrders.map((order) => (
                        <tr key={order.id}>
                          <td>
                            <span className="fw-semibold">{order.id}</span>
                          </td>
                          <td>{order.date}</td>
                          <td>{order.items} items</td>
                          <td>
                            <span className="fw-semibold">{order.total}</span>
                          </td>
                          <td>{getStatusBadge(order.status)}</td>
                          <td>
                            {order.trackingNumber ? (
                              <small className="text-muted font-monospace">
                                {order.trackingNumber}
                              </small>
                            ) : (
                              <span className="text-muted">-</span>
                            )}
                          </td>
                          <td>
                            <div className="btn-group btn-group-sm">
                              <button 
                                className="btn btn-outline-primary"
                                title="View Details"
                              >
                                <Eye size={14} />
                              </button>
                              <button 
                                className="btn btn-outline-secondary"
                                title="Download Invoice"
                              >
                                <Download size={14} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Orders;
