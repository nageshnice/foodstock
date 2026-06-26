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
  FormControl,
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
import { SearchOutlined, WarningAmberOutlined } from "@mui/icons-material";
import { api, apiError } from "../api";
import { PageHeader } from "../components/PageHeader";
import { usePolling } from "../hooks/usePolling";
import type { ApiResponse, Product, Variant } from "../types";

export function InventoryPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selected, setSelected] = useState<{ product: Product; variant: Variant } | null>(null);
  const [change, setChange] = useState(0);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Search & Filter State
  const [search, setSearch] = useState("");
  const [stockFilter, setStockFilter] = useState("all"); // 'all' | 'low' | 'healthy'

  // Pagination State
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get<ApiResponse<Product[]>>("/admin/products");
      setProducts(r.data.data);
      setError("");
    } catch (e) {
      setError(apiError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  usePolling(load, 12000);

  const adjust = async () => {
    if (!selected) return;
    if (change === 0) {
      setError("Quantity change must be non-zero");
      return;
    }
    if (!note.trim()) {
      setError("Please provide an adjustment reason");
      return;
    }

    try {
      await api.post(`/admin/inventory/${selected.variant.id}/adjust`, {
        quantity_change: change,
        note: note.trim(),
      });
      setSelected(null);
      setChange(0);
      setNote("");
      load();
    } catch (e) {
      setError(apiError(e));
    }
  };

  // Flatten products to variants for stock listing
  const allVariants = products.flatMap((p) =>
    p.variants.map((v) => ({
      product: p,
      variant: v,
    }))
  );

  // Filtering
  const filtered = allVariants.filter((item) => {
    const matchesSearch =
      item.product.name.toLowerCase().includes(search.toLowerCase()) ||
      item.product.sku.toLowerCase().includes(search.toLowerCase()) ||
      item.variant.size.toLowerCase().includes(search.toLowerCase());

    const isLow = item.variant.stock_quantity <= item.variant.low_stock_threshold;
    const matchesStock =
      stockFilter === "all" ||
      (stockFilter === "low" && isLow) ||
      (stockFilter === "healthy" && !isLow);

    return matchesSearch && matchesStock;
  });

  const pageCount = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  return (
    <>
      <PageHeader
        title="Stock & Inventory Control"
        subtitle="Manage physical pantry stocks, configure alerts, and log adjustments."
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
              placeholder="Search products by SKU, name, or size..."
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
              <InputLabel>Stock Level Status</InputLabel>
              <Select
                label="Stock Level Status"
                value={stockFilter}
                onChange={(e) => {
                  setStockFilter(e.target.value);
                  setPage(1);
                }}
              >
                <MenuItem value="all">All Levels</MenuItem>
                <MenuItem value="low">Low Stock Alerts</MenuItem>
                <MenuItem value="healthy">Healthy Levels</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      {/* Inventory table */}
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Product Details</TableCell>
              <TableCell>Variant Size</TableCell>
              <TableCell>Stock Count</TableCell>
              <TableCell>Warning Threshold</TableCell>
              <TableCell>Stock Status</TableCell>
              <TableCell align="right">Inventory Audit</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginated.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 6, color: "text.secondary" }}>
                  No stock items match your search filters.
                </TableCell>
              </TableRow>
            ) : (
              paginated.map(({ product, variant }) => {
                const isLow = variant.stock_quantity <= variant.low_stock_threshold;
                return (
                  <TableRow key={variant.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>
                        {product.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" fontFamily="monospace">
                        SKU: {product.sku}
                      </Typography>
                    </TableCell>
                    <TableCell>{variant.size}</TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>{variant.stock_quantity}</TableCell>
                    <TableCell color="text.secondary">{variant.low_stock_threshold}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        color={isLow ? "warning" : "success"}
                        icon={isLow ? <WarningAmberOutlined /> : undefined}
                        label={isLow ? `Low Stock Alert` : "Healthy"}
                        sx={{ fontWeight: "bold" }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => setSelected({ product, variant })}
                      >
                        Adjust Stock
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })
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

      {/* Adjust Dialog */}
      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)}>
        <DialogTitle>
          Stock adjustment: {selected?.product.name} ({selected?.variant.size})
        </DialogTitle>
        <DialogContent sx={{ display: "grid", gap: 2.5, pt: "16px !important", minWidth: 440 }}>
          <Typography variant="body2" color="text.secondary">
            Current stock: <b>{selected?.variant.stock_quantity}</b> units. Positive values add stock;
            negative values decrement stock.
          </Typography>

          <TextField
            label="Adjustment Quantity (+ or -)"
            type="number"
            value={change === 0 ? "" : change}
            onChange={(e) => setChange(Number(e.target.value))}
            autoFocus
          />

          <TextField
            label="Reason / Audit Note"
            placeholder="e.g. Received shipment, damaged stock, physical count match..."
            value={note}
            onChange={(e) => setNote(e.target.value)}
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelected(null)}>Cancel</Button>
          <Button variant="contained" onClick={adjust}>
            Save Adjustment
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
