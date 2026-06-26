import { useCallback, useState } from "react";
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import {
  Inventory2Outlined,
  CheckCircleOutline,
  WarningAmberOutlined,
  PeopleOutlined,
  ReceiptLongOutlined,
  CurrencyRupeeOutlined,
  PendingActionsOutlined,
  TrendingUpOutlined,
  ShoppingBagOutlined,
} from "@mui/icons-material";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, apiError } from "../api";
import { StatCard } from "../components/dashboard/StatCard";
import { PageHeader } from "../components/PageHeader";
import { useLiveDashboard } from "../hooks/useLiveDashboard";
import { usePolling } from "../hooks/usePolling";
import type { ApiResponse, DashboardData } from "../types";

const STATUS_COLORS: Record<string, string> = {
  placed: "#805ad5",
  confirmed: "#3182ce",
  processing: "#dd6b20",
  dispatched: "#2b6cb0",
  delivered: "#22734b",
  cancelled: "#c53030",
  returned: "#718096",
};

const formatCurrency = (value: number | string) =>
  `₹${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

const formatShortDate = (iso: string) =>
  new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [live, setLive] = useState(false);

  const fetchDashboard = useCallback(async () => {
    const r = await api.get<ApiResponse<DashboardData>>("/admin/dashboard");
    setData(r.data.data);
    setError("");
    return r.data.data;
  }, []);

  usePolling(
    async () => {
      try {
        await fetchDashboard();
      } catch (e) {
        setError(apiError(e));
      }
    },
    15000,
  );

  useLiveDashboard((payload) => {
    setData(payload);
    setLive(true);
  });

  const salesChartData =
    data?.sales_trend.map((point) => ({
      date: formatShortDate(point.date),
      revenue: Number(point.revenue),
      orders: point.orders,
    })) ?? [];

  const statusChartData =
    data?.orders_by_status.map((item) => ({
      name: item.status.replace("_", " "),
      value: item.count,
      status: item.status,
    })) ?? [];

  const topProductsData =
    data?.top_products.map((item) => ({
      name: item.name.length > 22 ? `${item.name.slice(0, 20)}…` : item.name,
      quantity: item.quantity,
      revenue: Number(item.revenue),
    })) ?? [];

  const fulfillmentRate =
    data && data.orders > 0
      ? Math.round(
          ((data.orders - (data.orders_by_status.find((s) => s.status === "cancelled")?.count ?? 0)) /
            data.orders) *
            100,
        )
      : 0;

  const secondaryMetrics = data
    ? [
        {
          label: "Active Products",
          value: data.active_products,
          total: data.products,
          color: "#22734b",
          icon: <CheckCircleOutline fontSize="small" />,
        },
        {
          label: "Low Stock Items",
          value: data.low_stock_variants,
          total: data.products,
          color: "#e8a317",
          icon: <WarningAmberOutlined fontSize="small" />,
        },
        {
          label: "Pending Orders",
          value: data.pending_orders,
          total: data.orders,
          color: "#805ad5",
          icon: <PendingActionsOutlined fontSize="small" />,
        },
        {
          label: "Catalog Size",
          value: data.products,
          total: data.products,
          color: "#1a365d",
          icon: <Inventory2Outlined fontSize="small" />,
        },
      ]
    : [];

  return (
    <>
      <PageHeader
        title="Store Analytics"
        subtitle="E-commerce performance overview — sales, orders, inventory, and customer activity."
        action={
          <Box display="flex" gap={1} alignItems="center">
            <Chip
              label={live ? "Live updates" : "Auto-refresh 15s"}
              color={live ? "success" : "primary"}
              size="small"
              variant="outlined"
              sx={{ fontWeight: 700 }}
            />
            <Chip
              icon={<TrendingUpOutlined />}
              label={`${fulfillmentRate}% fulfilment`}
              size="small"
              sx={{ fontWeight: 700, bgcolor: "rgba(34,115,75,.08)", color: "#22734b" }}
            />
          </Box>
        }
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }} onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2.5} mb={2.5}>
        {data ? (
          <>
            <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
              <StatCard
                label="Total Revenue"
                value={formatCurrency(data.revenue)}
                hint={`Today ${formatCurrency(data.today_revenue)}`}
                gradient="linear-gradient(135deg, #1a365d 0%, #2d5a9e 100%)"
                accent="rgba(255,255,255,.15)"
                icon={<CurrencyRupeeOutlined sx={{ color: "#fff", fontSize: 28 }} />}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
              <StatCard
                label="Total Orders"
                value={data.orders.toLocaleString("en-IN")}
                hint={`${data.today_orders} orders today`}
                gradient="linear-gradient(135deg, #28785f 0%, #35a07e 100%)"
                accent="rgba(255,255,255,.15)"
                icon={<ReceiptLongOutlined sx={{ color: "#fff", fontSize: 28 }} />}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
              <StatCard
                label="Customers"
                value={data.customers.toLocaleString("en-IN")}
                hint="Registered shoppers"
                gradient="linear-gradient(135deg, #553c9a 0%, #805ad5 100%)"
                accent="rgba(255,255,255,.15)"
                icon={<PeopleOutlined sx={{ color: "#fff", fontSize: 28 }} />}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, xl: 3 }}>
              <StatCard
                label="Avg Order Value"
                value={formatCurrency(data.avg_order_value)}
                hint="Per completed order"
                gradient="linear-gradient(135deg, #c05621 0%, #dd6b20 100%)"
                accent="rgba(255,255,255,.15)"
                icon={<ShoppingBagOutlined sx={{ color: "#fff", fontSize: 28 }} />}
              />
            </Grid>
          </>
        ) : (
          Array.from({ length: 4 }).map((_, i) => (
            <Grid size={{ xs: 12, sm: 6, xl: 3 }} key={i}>
              <Skeleton variant="rounded" height={120} sx={{ borderRadius: 4 }} />
            </Grid>
          ))
        )}
      </Grid>

      <Grid container spacing={2.5} mb={2.5}>
        {data
          ? secondaryMetrics.map((metric) => (
              <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={metric.label}>
                <Card sx={{ height: "100%" }}>
                  <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1.5}>
                      <Typography variant="body2" color="text.secondary" fontWeight={700}>
                        {metric.label}
                      </Typography>
                      <Box sx={{ color: metric.color }}>{metric.icon}</Box>
                    </Box>
                    <Typography variant="h5" fontWeight={800}>
                      {metric.value.toLocaleString("en-IN")}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={metric.total ? Math.min(100, (metric.value / metric.total) * 100) : 0}
                      sx={{
                        mt: 1.5,
                        height: 6,
                        borderRadius: 3,
                        bgcolor: "rgba(0,0,0,.04)",
                        "& .MuiLinearProgress-bar": { bgcolor: metric.color, borderRadius: 3 },
                      }}
                    />
                  </CardContent>
                </Card>
              </Grid>
            ))
          : Array.from({ length: 4 }).map((_, i) => (
              <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={i}>
                <Skeleton variant="rounded" height={100} sx={{ borderRadius: 4 }} />
              </Grid>
            ))}
      </Grid>

      <Grid container spacing={2.5} mb={2.5}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Card sx={{ height: "100%" }}>
            <CardContent>
              <Typography variant="h6" fontWeight={800} mb={0.5}>
                Sales Overview
              </Typography>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Revenue and order volume — last 7 days
              </Typography>
              {data ? (
                <Box sx={{ width: "100%", height: 300 }}>
                  <ResponsiveContainer>
                    <AreaChart data={salesChartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#2d5a9e" stopOpacity={0.35} />
                          <stop offset="95%" stopColor="#2d5a9e" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,.06)" />
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                      <YAxis
                        yAxisId="left"
                        tick={{ fontSize: 12 }}
                        tickFormatter={(v) => `₹${v}`}
                      />
                      <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
                      <Tooltip
                        formatter={(value, name) =>
                          name === "revenue"
                            ? [formatCurrency(Number(value)), "Revenue"]
                            : [value, "Orders"]
                        }
                      />
                      <Legend />
                      <Area
                        yAxisId="left"
                        type="monotone"
                        dataKey="revenue"
                        name="Revenue"
                        stroke="#1a365d"
                        fill="url(#revenueGradient)"
                        strokeWidth={2.5}
                      />
                      <Area
                        yAxisId="right"
                        type="monotone"
                        dataKey="orders"
                        name="Orders"
                        stroke="#35a07e"
                        fill="rgba(53,160,126,.08)"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </Box>
              ) : (
                <Skeleton variant="rounded" height={300} />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <Card sx={{ height: "100%" }}>
            <CardContent>
              <Typography variant="h6" fontWeight={800} mb={0.5}>
                Orders by Status
              </Typography>
              <Typography variant="body2" color="text.secondary" mb={1}>
                Pipeline breakdown
              </Typography>
              {data ? (
                statusChartData.length > 0 ? (
                  <Box sx={{ width: "100%", height: 300 }}>
                    <ResponsiveContainer>
                      <PieChart>
                        <Pie
                          data={statusChartData}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          innerRadius={55}
                          outerRadius={90}
                          paddingAngle={3}
                        >
                          {statusChartData.map((entry) => (
                            <Cell
                              key={entry.status}
                              fill={STATUS_COLORS[entry.status] ?? "#94a3b8"}
                            />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend layout="horizontal" verticalAlign="bottom" />
                      </PieChart>
                    </ResponsiveContainer>
                  </Box>
                ) : (
                  <Box py={8} textAlign="center" color="text.secondary">
                    No orders yet
                  </Box>
                )
              ) : (
                <Skeleton variant="rounded" height={300} />
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card sx={{ height: "100%" }}>
            <CardContent>
              <Typography variant="h6" fontWeight={800} mb={0.5}>
                Top Selling Products
              </Typography>
              <Typography variant="body2" color="text.secondary" mb={2}>
                By units sold (all time)
              </Typography>
              {data ? (
                topProductsData.length > 0 ? (
                  <Box sx={{ width: "100%", height: 280 }}>
                    <ResponsiveContainer>
                      <BarChart data={topProductsData} layout="vertical" margin={{ left: 8 }}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                        <XAxis type="number" tick={{ fontSize: 12 }} />
                        <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} />
                        <Tooltip
                          formatter={(value, name) =>
                            name === "revenue"
                              ? [formatCurrency(Number(value)), "Revenue"]
                              : [value, "Units"]
                          }
                        />
                        <Bar dataKey="quantity" name="Units" fill="#2d5a9e" radius={[0, 6, 6, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                ) : (
                  <Box py={8} textAlign="center" color="text.secondary">
                    No product sales yet
                  </Box>
                )
              ) : (
                <Skeleton variant="rounded" height={280} />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 7 }}>
          <Card>
            <CardContent sx={{ p: 0, "&:last-child": { pb: 0 } }}>
              <Box px={2.5} pt={2.5} pb={1.5}>
                <Typography variant="h6" fontWeight={800}>
                  Recent Orders
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Latest transactions across the store
                </Typography>
              </Box>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Order</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell align="right">Amount</TableCell>
                      <TableCell>Placed</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {!data ? (
                      <TableRow>
                        <TableCell colSpan={4}>
                          <Skeleton height={40} />
                        </TableCell>
                      </TableRow>
                    ) : data.recent_orders.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} align="center" sx={{ py: 6, color: "text.secondary" }}>
                          No orders yet
                        </TableCell>
                      </TableRow>
                    ) : (
                      data.recent_orders.map((order) => (
                        <TableRow key={order.id} hover>
                          <TableCell sx={{ fontWeight: 700 }}>{order.order_number}</TableCell>
                          <TableCell>
                            <Chip
                              label={order.status.replace("_", " ")}
                              size="small"
                              sx={{
                                fontWeight: 700,
                                textTransform: "capitalize",
                                bgcolor: `${STATUS_COLORS[order.status] ?? "#94a3b8"}18`,
                                color: STATUS_COLORS[order.status] ?? "#64748b",
                                border: `1px solid ${STATUS_COLORS[order.status] ?? "#94a3b8"}40`,
                              }}
                            />
                          </TableCell>
                          <TableCell align="right" sx={{ fontWeight: 700 }}>
                            {formatCurrency(order.total_amount)}
                          </TableCell>
                          <TableCell>
                            {new Date(order.placed_at).toLocaleString("en-IN", {
                              day: "numeric",
                              month: "short",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </>
  );
}
