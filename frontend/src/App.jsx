import "bootstrap/dist/js/bootstrap.bundle.min.js";{/* lesson 22 */}
import { Route, BrowserRouter as Router, Routes } from "react-router-dom"; {/* lesson 22 */}
import "./App.css"; {/* lesson 22 */}
import Cart from "./pages/Cart";
import Checkout from "./pages/Checkout";
import Dashboard from "./pages/Dashboard";
import DashboardHome from "./pages/DashboardHome";
import { Home } from "./pages/Home"; {/* lesson 22 */}
import Login from "./pages/Login";
import Orders from "./pages/Orders";
import ProductDetail from "./pages/ProductDetails";
import ProfileSettings from "./pages/ProfileSetting";
import Register from "./pages/Register"; {/* lesson 24 */}
import OrderSuccess from "./pages/OrderSuccess";

function App() {
  return (
    <>
      <Router> {/* lesson 22 */}
        <Routes> {/* lesson 22 */}
          <Route path="/" element={<Home />} /> {/* lesson 22 */}
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Register />} />  {/* lesson 24 */} 
          <Route path="/dashboard" element={<Dashboard />}>
            <Route index element={<DashboardHome />} />
            <Route path="profile" element={<ProfileSettings />} />
            <Route path="orders" element={<Orders />} />
          </Route>
          <Route path="/order/success" element={<OrderSuccess />} />
        </Routes>
      </Router>
    </>
  );
}

export default App;
