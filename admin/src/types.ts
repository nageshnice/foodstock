export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface AdminProfile {
  id: number;
  email: string;
  full_name: string | null;
  phone?: string | null;
  image_url?: string | null;
  role: string;
}

export interface AdminAlert {
  id: string;
  severity: string;
  title: string;
  message: string;
  href?: string | null;
}

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  phone?: string | null;
  image_url?: string | null;
  role: string;
  is_active?: boolean;
  created_at?: string;
  addresses_count?: number;
  orders_count?: number;
  total_spent?: string;
}

export interface Entity {
  id: number;
  name: string;
  is_active: boolean;
  product_count?: number;
  subtitle?: string | null;
}

export interface Variant {
  id: number;
  size: string;
  mrp: string;
  price: string;
  stock_quantity: number;
  low_stock_threshold: number;
  is_active: boolean;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  source_section: string | null;
  description: string | null;
  image_url: string | null;
  tax_rate: string;
  is_active: boolean;
  region_id: number | null;
  category_id: number | null;
  brand_id: number | null;
  vendor_id: number | null;
  region_name: string | null;
  category_name: string | null;
  brand_name: string | null;
  vendor_name: string | null;
  variants: Variant[];
}

export interface OrderItem {
  product_name: string;
  variant_size: string;
  unit_price: string;
  quantity: number;
  line_total: string;
}

export interface Order {
  id: number;
  order_number: string;
  status: string;
  payment_method: string;
  subtotal: string;
  tax_amount: string;
  delivery_fee: string;
  discount_amount: string;
  total_amount: string;
  delivery_address: string;
  placed_at: string;
  items: OrderItem[];
}

export interface Vendor {
  id: number;
  name: string;
  is_active: boolean;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  tax_identifier: string | null;
}

export interface Customer {
  id: number;
  email: string;
  full_name: string | null;
  phone: string | null;
  image_url?: string | null;
  role: string;
  is_active: boolean;
  created_at?: string;
  addresses_count?: number;
  orders_count?: number;
  total_spent?: string;
}

export interface DailySalesPoint {
  date: string;
  orders: number;
  revenue: string;
}

export interface StatusBreakdown {
  status: string;
  count: number;
}

export interface TopProductSummary {
  name: string;
  quantity: number;
  revenue: string;
}

export interface DashboardData {
  products: number;
  active_products: number;
  low_stock_variants: number;
  customers: number;
  orders: number;
  revenue: string;
  pending_orders: number;
  today_orders: number;
  today_revenue: string;
  avg_order_value: string;
  sales_trend: DailySalesPoint[];
  orders_by_status: StatusBreakdown[];
  top_products: TopProductSummary[];
  recent_orders: Array<{
    id: number;
    order_number: string;
    status: string;
    total_amount: string;
    placed_at: string;
  }>;
}
