import { useCallback, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Pagination,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { SearchOutlined, VisibilityOutlined } from "@mui/icons-material";
import { api, apiError } from "../api";
import { PageHeader } from "../components/PageHeader";
import { usePolling } from "../hooks/usePolling";
import type { ApiResponse, Order } from "../types";

const statuses = [
  "placed",
  "confirmed",
  "packing",
  "out_for_delivery",
  "delivered",
  "cancelled",
];

const statusColors: Record<string, "default" | "primary" | "secondary" | "warning" | "success" | "error"> = {
  placed: "warning",
  confirmed: "primary",
  packing: "secondary",
  out_for_delivery: "info" as any, // falls back nicely
  delivered: "success",
  cancelled: "error",
};

export function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selected, setSelected] = useState<Order | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Search & Filter State
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // Pagination State
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get<ApiResponse<Order[]>>("/admin/orders");
      setOrders(r.data.data);
      setError("");
    } catch (e) {
      setError(apiError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  usePolling(load, 12000);

  const update = async (id: number, status: string) => {
    try {
      await api.patch(`/admin/orders/${id}/status`, { status });
      load();
      if (selected && selected.id === id) {
        setSelected((prev) => (prev ? { ...prev, status } : null));
      }
    } catch (e) {
      setError(apiError(e));
    }
  };

  // Filter logic
  const filtered = orders.filter((o) => {
    const matchesSearch =
      o.order_number.toLowerCase().includes(search.toLowerCase()) ||
      o.delivery_address.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = !statusFilter || o.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const pageCount = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  return (
    <>
      <PageHeader
        title="Pantry Orders"
        subtitle="Manage customer checkout orders, track status updates, and view invoices."
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }} onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      {/* Filter toolbar */}
      <Card sx={{ mb: 4 }}>
        <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
          <Box display="flex" gap={2} flexWrap="wrap">
            <TextField
              size="small"
              placeholder="Search by order number or address..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              sx={{ flex: 1, minWidth: 260 }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchOutlined fontSize="small" />
                    </InputAdornment>
                  ),
                },
              }}
            />

            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>Order Status</InputLabel>
              <Select
                label="Order Status"
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
              >
                <MenuItem value="">All Statuses</MenuItem>
                {statuses.map((status) => (
                  <MenuItem key={status} value={status}>
                    {status.replaceAll("_", " ").toUpperCase()}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      {/* Orders Table */}
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Order Number</TableCell>
              <TableCell>Placed Date & Time</TableCell>
              <TableCell>Delivery Address Summary</TableCell>
              <TableCell>Invoice Value</TableCell>
              <TableCell>Status Tracker</TableCell>
              <TableCell align="right">View Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginated.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 6, color: "text.secondary" }}>
                  No orders match the selected search parameters.
                </TableCell>
              </TableRow>
            ) : (
              paginated.map((order) => (
                <TableRow key={order.id} hover>
                  <TableCell sx={{ fontWeight: "bold", fontFamily: "monospace" }}>
                    {order.order_number}
                  </TableCell>
                  <TableCell>{new Date(order.placed_at).toLocaleString()}</TableCell>
                  <TableCell>
                    <Typography
                      variant="body2"
                      noWrap
                      sx={{ maxWidth: 280, textOverflow: "ellipsis" }}
                    >
                      {order.delivery_address}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ fontWeight: "bold" }}>
                    ₹{Number(order.total_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell>
                    <Select
                      size="small"
                      value={order.status}
                      onChange={(e) => update(order.id, e.target.value)}
                      sx={{ minWidth: 160 }}
                    >
                      {statuses.map((st) => (
                        <MenuItem value={st} key={st}>
                          <Chip
                            size="small"
                            color={statusColors[st] || "default"}
                            label={st.replaceAll("_", " ").toUpperCase()}
                            sx={{ fontWeight: "bold" }}
                          />
                        </MenuItem>
                      ))}
                    </Select>
                  </TableCell>
                  <TableCell align="right">
                    <IconButton color="primary" onClick={() => setSelected(order)}>
                      <VisibilityOutlined />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {pageCount > 1 && (
        <Box display="flex" justifyContent="center" mt={3} mb={5}>
          <Pagination
            count={pageCount}
            page={page}
            onChange={(_, val) => setPage(val)}
            color="primary"
          />
        </Box>
      )}

      {/* Invoice Details Dialog */}
      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} fullWidth maxWidth="sm">
        <DialogTitle>Order Summary: #{selected?.order_number}</DialogTitle>
        <DialogContent dividers>
          {selected && (
            <Box display="flex" flexDirection="column" gap={2}>
              <Box display="flex" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Placed Date
                  </Typography>
                  <Typography variant="body1" fontWeight={600}>
                    {new Date(selected.placed_at).toLocaleString()}
                  </Typography>
                </Box>
                <Box alignSelf="center">
                  <Select
                    size="small"
                    value={selected.status}
                    onChange={(e) => update(selected.id, e.target.value)}
                  >
                    {statuses.map((st) => (
                      <MenuItem value={st} key={st}>
                        {st.replaceAll("_", " ").toUpperCase()}
                      </MenuItem>
                    ))}
                  </Select>
                </Box>
              </Box>

              <Divider />

              <Typography variant="subtitle2" fontWeight={700} color="primary">
                Delivery Address
              </Typography>
              <Typography variant="body2">{selected.delivery_address}</Typography>

              <Divider />

              <Typography variant="subtitle2" fontWeight={700} color="primary">
                Order Items
              </Typography>
              <Box display="flex" flexDirection="column" gap={1.5}>
                {selected.items.map((item, idx) => (
                  <Box key={idx} display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="body2" fontWeight={600}>
                        {item.product_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Size: {item.variant_size} | Qty: {item.quantity}
                      </Typography>
                    </Box>
                    <Typography variant="body2" fontWeight={600}>
                      ₹{Number(item.line_total).toFixed(2)}
                    </Typography>
                  </Box>
                ))}
              </Box>

              <Divider />

              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Subtotal</Typography>
                  <Typography variant="body2">₹{Number(selected.subtotal).toFixed(2)}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">GST Tax</Typography>
                  <Typography variant="body2">₹{Number(selected.tax_amount).toFixed(2)}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Delivery Fee</Typography>
                  <Typography variant="body2">₹{Number(selected.delivery_fee).toFixed(2)}</Typography>
                </Box>
                {Number(selected.discount_amount) > 0 && (
                  <Box display="flex" justifyContent="space-between" color="success.main">
                    <Typography variant="body2">Discount</Typography>
                    <Typography variant="body2">-₹{Number(selected.discount_amount).toFixed(2)}</Typography>
                  </Box>
                )}
                <Box display="flex" justifyContent="space-between" fontWeight="bold">
                  <Typography variant="body1">Total Invoice Value</Typography>
                  <Typography variant="body1">₹{Number(selected.total_amount).toFixed(2)}</Typography>
                </Box>
              </Box>

              <Divider />
              <Typography variant="body2" color="text.secondary">
                Payment Method: <b>{selected.payment_method.replaceAll("_", " ").toUpperCase()}</b>
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelected(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
