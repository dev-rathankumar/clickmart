import React from "react";
import { Link } from "react-router-dom";
import Header from "../components/Navbar";

const OrderSuccess = () => {
  return (
    <>
    <Header/>
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-lg-8">
          {/* Success Header */}
          <div className="text-center mb-5">
            <div className="mb-4">
              <i
                className="bi bi-check-circle-fill text-success"
                style={{ fontSize: "4rem" }}
              ></i>
            </div>
            <h1 className="display-5 fw-bold text-success mb-3">
              Order Confirmed!
            </h1>
            <p className="lead text-muted">
              Thank you for your purchase. Your order has been successfully
              placed and is being processed.
            </p>
          </div>

          {/* Order Details */}
          <div className="card mb-4">
            <div className="card-header bg-success text-white d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Order Details</h5>
              <span className="badge bg-light text-dark">#123456</span>
            </div>
            <div className="card-body">
              <div className="row mb-4">
                <div className="col-md-6">
                  <h6 className="text-muted mb-2">Order Date</h6>
                  <p className="mb-0">Friday, September 19, 2025</p>
                </div>
                <div className="col-md-6">
                  <h6 className="text-muted mb-2">Estimated Delivery</h6>
                  <p className="mb-0 text-primary fw-semibold">
                    Wednesday, September 24, 2025
                  </p>
                </div>
              </div>

              <div className="row">
                <div className="col-md-6">
                  <h6 className="text-muted mb-2">Order Status</h6>
                  <span className="badge bg-warning text-dark">
                    <i className="bi bi-clock me-1"></i>
                    Pending
                  </span>
                </div>
                <div className="col-md-6">
                  <h6 className="text-muted mb-2">Payment Method</h6>
                  <p className="mb-0">
                    <i className="bi bi-credit-card me-2"></i>
                    **** **** **** 1234
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Order Items */}
          <div className="card mb-4">
            <div className="card-header">
              <h5 className="mb-0">Order Items</h5>
            </div>
            <div className="card-body p-0">
              <table className="table table-responsive mb-0">
                <thead className="bg-light">
                  <tr>
                    <th>Product</th>
                    <th>Price</th>
                    <th>Quantity</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>
                      <div className="d-flex align-items-center">
                        <img
                          src="https://via.placeholder.com/50"
                          alt="Product"
                          style={{
                            width: "50px",
                            height: "50px",
                            objectFit: "cover",
                          }}
                          className="rounded me-3"
                        />
                        <div>
                          <h6 className="mb-1">Wireless Headphones</h6>
                          <small className="text-muted">Electronics</small>
                        </div>
                      </div>
                    </td>
                    <td className="align-middle">$99.00</td>
                    <td className="align-middle">2</td>
                    <td className="align-middle fw-semibold">$198.00</td>
                  </tr>
                  <tr>
                    <td>
                      <div className="d-flex align-items-center">
                        <img
                          src="https://via.placeholder.com/50"
                          alt="Product"
                          style={{
                            width: "50px",
                            height: "50px",
                            objectFit: "cover",
                          }}
                          className="rounded me-3"
                        />
                        <div>
                          <h6 className="mb-1">Smart Watch</h6>
                          <small className="text-muted">Accessories</small>
                        </div>
                      </div>
                    </td>
                    <td className="align-middle">$150.00</td>
                    <td className="align-middle">1</td>
                    <td className="align-middle fw-semibold">$150.00</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Order Summary */}
          <div className="card mb-4">
            <div className="card-header">
              <h5 className="mb-0">Order Summary</h5>
            </div>
            <div className="card-body">
              <div className="d-flex justify-content-between mb-2">
                <span>Subtotal:</span>
                <span>$348.00</span>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span>Shipping:</span>
                <span>FREE</span>
              </div>
              <div className="d-flex justify-content-between mb-3">
                <span>Tax:</span>
                <span>$20.00</span>
              </div>
              <hr />
              <div className="d-flex justify-content-between">
                <strong>Total:</strong>
                <strong className="text-success h5">$368.00</strong>
              </div>
            </div>
          </div>

          {/* Shipping Address */}
          <div className="card mb-4">
            <div className="card-header">
              <h5 className="mb-0">Shipping Address</h5>
            </div>
            <div className="card-body">
              <address className="mb-0">
                <strong>John Doe</strong>
                <br />
                123 Main Street
                <br />
                New York, NY 10001
                <br />
                USA
                <br />
                <abbr title="Phone">P:</abbr> +1 555 123 4567
                <br />
                <abbr title="Email">E:</abbr> john.doe@example.com
              </address>
            </div>
          </div>

          {/* Next Steps */}
          <div className="alert alert-info">
            <h6 className="alert-heading">What's Next?</h6>
            <ul className="mb-0">
              <li>You'll receive an email confirmation shortly</li>
              <li>We'll send you tracking information once your order ships</li>
              <li>Your order will be delivered by Wednesday, September 24, 2025</li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="text-center">
            <Link to="/" className="btn btn-primary btn-lg me-3">
              <i className="bi bi-house me-2"></i>
              Continue Shopping
            </Link>
            <button
              className="btn btn-outline-primary btn-lg"
              onClick={() => window.print()}
            >
              <i className="bi bi-printer me-2"></i>
              Print Order
            </button>
          </div>
        </div>
      </div>
    </div>
    </>
  );
};

export default OrderSuccess;
