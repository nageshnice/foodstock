import { useCallback, useState } from "react";
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
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
} from "@mui/icons-material";
import { api, apiError } from "../api";
import { PageHeader } from "../components/PageHeader";
import { useLiveDashboard } from "../hooks/useLiveDashboard";
import { usePolling } from "../hooks/usePolling";
import type { ApiResponse } from "../types";

interface Dashboard {
  products: number;
  active_products: number;
  low_stock_variants: number;
  customers: number;
  orders: number;
  revenue: string;
  pending_orders: number;
  recent_orders: Array<{
    id: number;
    order_number: string;
    status: string;
    total_amount: string;
    placed_at: string;
  }>;
}

export function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  const [live, setLive] = useState(false);

  const fetchDashboard = useCallback(async () => {
    const r = await api.get<ApiResponse<Dashboard>>("/admin/dashboard");
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

  const cards = data
    ? [
        {
          label: "Total Products",
          value: data.products,
          icon: <Inventory2Outlined sx={{ fontSize: 32, color: "#1a365d" }} />,
          bg: "rgba(26,54,93,0.04)",
        },
        {
          label: "Live Catalog Items",
          value: data.active_products,
          icon: <CheckCircleOutline sx={{ fontSize: 32, color: "#22734b" }} />,
          bg: "rgba(34,115,75,0.04)",
        },
        {
          label: "Low Stock Warning",
          value: data.low_stock_variants,
          icon: <WarningAmberOutlined sx={{ fontSize: 32, color: "#e8a317" }} />,
          bg: "rgba(232,163,23,0.04)",
        },
        {
          label: "Pending Orders",
          value: data.pending_orders,
          icon: <PendingActionsOutlined sx={{ fontSize: 32, color: "#805ad5" }} />,
          bg: "rgba(128,90,213,0.04)",
        },
        {
          label: "Registered Customers",
          value: data.customers,
          icon: <PeopleOutlined sx={{ fontSize: 32, color: "#2d5a9e" }} />,
          bg: "rgba(45,90,158,0.04)",
        },
        {
          label: "Total Fulfilment Orders",
          value: data.orders,
          icon: <ReceiptLongOutlined sx={{ fontSize: 32, color: "#28785f" }} />,
          bg: "rgba(40,120,95,0.04)",
        },
        {
          label: "Gross Revenue Sales",
          value: `₹${Number(data.revenue).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`,
          icon: <CurrencyRupeeOutlined sx={{ fontSize: 32, color: "#c53030" }} />,
          bg: "rgba(197,48,48,0.04)",
        },
      ]
    : [];

  return (
    <>
      <PageHeader
        title="Overview Dashboard"
        subtitle="Live monitoring of catalog, inventory, and orders — auto-refreshes every 15 seconds."
        action={
          live ? (
            <Chip label="Live" color="success" size="small" variant="outlined" />
          ) : (
            <Chip label="Polling" color="primary" size="small" variant="outlined" />
          )
        }
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {data
          ? cards.map(({ label, value, icon, bg }) => (
              <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={label}>
                <Card
                  sx={{
                    borderLeft: "4px solid",
                    borderLeftColor: (icon.props.sx?.color || "#1a365d") as string,
                  }}
                >
                  <CardContent
                    sx={{
                      p: 2,
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      "&:last-child": { pb: 2 },
                    }}
                  >
                    <Box>
                      <Typography color="text.secondary" variant="caption" fontWeight={700}>
                        {label}
                      </Typography>
                      <Typography variant="h5" fontWeight={900} mt={0.5}>
                        {value}
                      </Typography>
                    </Box>
                    <Box
                      sx={{
                        width: 44,
                        height: 44,
                        borderRadius: 2,
                        bgcolor: bg,
                        display: "grid",
                        placeItems: "center",
                        flexShrink: 0,
                      }}
                    >
                      {icon}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))
          : Array.from({ length: 7 }).map((_, index) => (
              <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={index}>
                <Skeleton variant="rounded" height={96} sx={{ borderRadius: 3 }} />
              </Grid>
            ))}
      </Grid>

      {data && data.recent_orders.length > 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" fontWeight={800} mb={2}>
              Recent Orders
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Order #</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell>Placed</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.recent_orders.map((order) => (
                    <TableRow key={order.id}>
                      <TableCell>{order.order_number}</TableCell>
                      <TableCell>
                        <Chip label={order.status} size="small" />
                      </TableCell>
                      <TableCell align="right">
                        ₹{Number(order.total_amount).toLocaleString("en-IN")}
                      </TableCell>
                      <TableCell>{new Date(order.placed_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </>
  );
}
