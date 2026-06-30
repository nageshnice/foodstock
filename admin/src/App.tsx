import { Navigate, Route, Routes } from "react-router-dom";
import { clearAuthSession, getStoredToken, isAuthenticated } from "./authSession";
import { AdminLayout } from "./components/AdminLayout";
import { CatalogPage } from "./pages/CatalogPage";
import { CustomersPage } from "./pages/CustomersPage";
import { DashboardPage } from "./pages/DashboardPage";
import { InventoryPage } from "./pages/InventoryPage";
import { LoginPage } from "./pages/LoginPage";
import { OrdersPage } from "./pages/OrdersPage";
import { ProductsPage } from "./pages/ProductsPage";
import { VendorsPage } from "./pages/VendorsPage";

function ProtectedLayout() {
  if (!isAuthenticated()) {
    const hadToken = Boolean(getStoredToken());
    if (hadToken) clearAuthSession();
    return (
      <Navigate to={hadToken ? "/login?session=expired" : "/login"} replace />
    );
  }
  return <AdminLayout />;
}

export default function App() {
  return <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route element={<ProtectedLayout />}>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/products" element={<ProductsPage />} />
      <Route path="/inventory" element={<InventoryPage />} />
      <Route path="/orders" element={<OrdersPage />} />
      <Route path="/customers" element={<CustomersPage />} />
      <Route path="/vendors" element={<VendorsPage />} />
      <Route path="/catalog" element={<CatalogPage />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>;
}
