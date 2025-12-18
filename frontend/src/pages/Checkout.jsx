import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";

import { toast } from "react-toastify";

const Checkout = () => {
  const { state: cartState, clearCart } = useCart();
  const navigate = useNavigate();

  const [currentStep, setCurrentStep] = useState(1);
  const [shippingAddress, setShippingAddress] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    address: "",
    city: "",
    state: "",
    zipCode: "",
    country: "United States",
  });

  const [errors, setErrors] = useState({});
  const [isProcessing, setIsProcessing] = useState(false);

  // Redirect if cart is empty
  if (cartState.items.length === 0) {
    return (
      <div className="container py-5">
        <div className="alert alert-warning text-center">
          <h4>Your cart is empty</h4>
          <p>Add some items to your cart before proceeding to checkout.</p>
          <button className="btn btn-primary" onClick={() => navigate("/")}>
            Continue Shopping
          </button>
        </div>
      </div>
    );
  }

  const subtotal = cartState.total;
  const tax = subtotal * 0.08;
  const total = subtotal + tax ;

  const validateShippingForm = () => {
    const newErrors = {};
    if (!shippingAddress.firstName.trim())
      newErrors.firstName = "First name is required";
    if (!shippingAddress.lastName.trim())
      newErrors.lastName = "Last name is required";
    if (!shippingAddress.email.trim()) newErrors.email = "Email is required";
    else if (!/\S+@\S+\.\S+/.test(shippingAddress.email))
      newErrors.email = "Email is invalid";
    if (!shippingAddress.phone.trim()) newErrors.phone = "Phone is required";
    if (!shippingAddress.address.trim())
      newErrors.address = "Address is required";
    if (!shippingAddress.city.trim()) newErrors.city = "City is required";
    if (!shippingAddress.state.trim()) newErrors.state = "State is required";
    if (!shippingAddress.zipCode.trim())
      newErrors.zipCode = "ZIP code is required";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleShippingSubmit = (e) => {
    e.preventDefault();
    if (validateShippingForm()) setCurrentStep(2);
  };

  const handlePaymentSubmit = async (e) => {
    e.preventDefault();
    if (!validatePaymentForm()) return;

    setIsProcessing(true);
    try {
      const result = "";
      return;
      if (result.success) {
        clearCart();
        toast.success("Order placed successfully!");
        navigate(`/order-success/${result.orderId}`);
      } else {
        toast.error(result.error || "Payment failed");
        navigate(
          `/order-failure?error=${encodeURIComponent(
            result.error || "Payment failed"
          )}`
        );
      }
    } catch (error) {
      toast.error("An unexpected error occurred");
      navigate("/order-failure?error=An unexpected error occurred");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="container py-5">
      <div className="row mb-4">
        <div className="col">
          <h1 className="display-5 fw-bold">Checkout</h1>
          <div className="d-flex align-items-center mb-3">
            <div
              className={`badge ${
                currentStep >= 1 ? "bg-primary" : "bg-secondary"
              } me-2`}
            >
              1
            </div>
            <span
              className={
                currentStep >= 1 ? "text-primary fw-semibold" : "text-muted"
              }
            >
              Shipping
            </span>
            <i className="bi bi-arrow-right mx-2 text-muted"></i>
            <div
              className={`badge ${
                currentStep >= 2 ? "bg-primary" : "bg-secondary"
              } me-2`}
            >
              2
            </div>
            <span
              className={
                currentStep >= 2 ? "text-primary fw-semibold" : "text-muted"
              }
            >
              Payment
            </span>
          </div>
        </div>
      </div>

      <div className="row">
        {/* Left section */}
        <div className="col-lg-8">
          {currentStep === 1 && (
            <div className="card mb-4">
              <div className="card-header">
                <h5 className="mb-0">Shipping Information</h5>
              </div>
              <div className="card-body">
                <form onSubmit={handleShippingSubmit}>
                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label className="form-label">First Name *</label>
                      <input
                        type="text"
                        className={`form-control ${
                          errors.firstName ? "is-invalid" : ""
                        }`}
                        value={shippingAddress.firstName}
                        onChange={(e) =>
                          setShippingAddress({
                            ...shippingAddress,
                            firstName: e.target.value,
                          })
                        }
                      />
                      <div className="invalid-feedback">{errors.firstName}</div>
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label">Last Name *</label>
                      <input
                        type="text"
                        className={`form-control ${
                          errors.lastName ? "is-invalid" : ""
                        }`}
                        value={shippingAddress.lastName}
                        onChange={(e) =>
                          setShippingAddress({
                            ...shippingAddress,
                            lastName: e.target.value,
                          })
                        }
                      />
                      <div className="invalid-feedback">{errors.lastName}</div>
                    </div>
                  </div>

                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label className="form-label">Email *</label>
                      <input
                        type="email"
                        className={`form-control ${
                          errors.email ? "is-invalid" : ""
                        }`}
                        value={shippingAddress.email}
                        onChange={(e) =>
                          setShippingAddress({
                            ...shippingAddress,
                            email: e.target.value,
                          })
                        }
                      />
                      <div className="invalid-feedback">{errors.email}</div>
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label">Phone *</label>
                      <input
                        type="tel"
                        className={`form-control ${
                          errors.phone ? "is-invalid" : ""
                        }`}
                        value={shippingAddress.phone}
                        onChange={(e) =>
                          setShippingAddress({
                            ...shippingAddress,
                            phone: e.target.value,
                          })
                        }
                      />
                      <div className="invalid-feedback">{errors.phone}</div>
                    </div>
                  </div>

                  <div className="mb-3">
                    <label className="form-label">Address *</label>
                    <input
                      type="text"
                      className={`form-control ${
                        errors.address ? "is-invalid" : ""
                      }`}
                      value={shippingAddress.address}
                      onChange={(e) =>
                        setShippingAddress({
                          ...shippingAddress,
                          address: e.target.value,
                        })
                      }
                    />
                    <div className="invalid-feedback">{errors.address}</div>
                  </div>

                  <div className="row">
                    <div className="col-md-4 mb-3">
                      <label className="form-label">City *</label>
                      <input
                        type="text"
                        className={`form-control ${
                          errors.city ? "is-invalid" : ""
                        }`}
                        value={shippingAddress.city}
                        onChange={(e) =>
                          setShippingAddress({
                            ...shippingAddress,
                            city: e.target.value,
                          })
                        }
                      />
                      <div className="invalid-feedback">{errors.city}</div>
                    </div>
                    <div className="col-md-4 mb-3">
                      <label className="form-label">State *</label>
                      <input
                        type="text"
                        className={`form-control ${
                          errors.state ? "is-invalid" : ""
                        }`}
                        value={shippingAddress.state}
                        onChange={(e) =>
                          setShippingAddress({
                            ...shippingAddress,
                            state: e.target.value,
                          })
                        }
                      />
                      <div className="invalid-feedback">{errors.state}</div>
                    </div>
                    <div className="col-md-4 mb-3">
                      <label className="form-label">ZIP Code *</label>
                      <input
                        type="text"
                        className={`form-control ${
                          errors.zipCode ? "is-invalid" : ""
                        }`}
                        value={shippingAddress.zipCode}
                        onChange={(e) =>
                          setShippingAddress({
                            ...shippingAddress,
                            zipCode: e.target.value,
                          })
                        }
                      />
                      <div className="invalid-feedback">{errors.zipCode}</div>
                    </div>
                  </div>

                  <div className="d-flex justify-content-between">
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={() => navigate("/cart")}
                    >
                      <i className="bi bi-arrow-left me-2"></i>Back to Cart
                    </button>
                    <button type="submit" className="btn btn-primary">
                      Continue to Payment{" "}
                      <i className="bi bi-arrow-right ms-2"></i>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>

        {/* Right section */}
        <div className="col-lg-4">
          <div className="card sticky-top" style={{ top: "100px" }}>
            <div className="card-header">
              <h5 className="mb-0">Order Summary</h5>
            </div>
            <div className="card-body">
              <div className="mb-3">
                {cartState.items.map((item) => (
                  <div
                    key={item.id}
                    className="d-flex justify-content-between align-items-center mb-2"
                  >
                    <div className="d-flex align-items-center">
                      <img
                        src={item.image}
                        alt={item.name}
                        style={{
                          width: "40px",
                          height: "40px",
                          objectFit: "cover",
                        }}
                        className="rounded me-2"
                      />
                      <div>
                        <small className="fw-semibold">{item.name}</small>
                        <br />
                        <small className="text-muted">
                          Qty: {item.quantity}
                        </small>
                      </div>
                    </div>
                    <small className="fw-semibold">
                      ${(item.price * item.quantity).toFixed(2)}
                    </small>
                  </div>
                ))}
              </div>

              <hr />

              <div className="d-flex justify-content-between mb-2">
                <span>Subtotal:</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span>Shipping:</span>
                <span>
                  Free
                </span>
              </div>
              <div className="d-flex justify-content-between mb-3">
                <span>Tax:</span>
                <span>${tax.toFixed(2)}</span>
              </div>

              <hr />

              <div className="d-flex justify-content-between mb-3">
                <strong>Total:</strong>
                <strong className="text-primary h5">${total.toFixed(2)}</strong>
              </div>

              <div className="text-center text-muted">
                <small>
                  <i className="bi bi-shield-check me-1"></i>
                  Secure checkout with SSL encryption
                </small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Checkout;
