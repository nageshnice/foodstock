import { useEffect, useState } from "react";
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
  FormControlLabel,
  IconButton,
  InputAdornment,
  Pagination,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { AddCircleOutline, EditOutlined, SearchOutlined } from "@mui/icons-material";
import { api, apiError } from "../api";
import { PageHeader } from "../components/PageHeader";
import type { ApiResponse, Vendor } from "../types";

const emptyVendor = {
  name: "",
  contact_name: "",
  email: "",
  phone: "",
  address: "",
  tax_identifier: "",
  is_active: true,
};

export function VendorsPage() {
  const [items, setItems] = useState<Vendor[]>([]);
  const [form, setForm] = useState(emptyVendor);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Search & Pagination State
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get<ApiResponse<Vendor[]>>("/admin/vendors");
      setItems(r.data.data);
    } catch (e) {
      setError(apiError(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const begin = (item?: Vendor) => {
    setError("");
    if (item) {
      setEditingId(item.id);
      setForm({
        name: item.name,
        contact_name: item.contact_name ?? "",
        email: item.email ?? "",
        phone: item.phone ?? "",
        address: item.address ?? "",
        tax_identifier: item.tax_identifier ?? "",
        is_active: item.is_active,
      });
    } else {
      setEditingId(null);
      setForm(emptyVendor);
    }
    setOpen(true);
  };

  const save = async () => {
    setError("");
    if (!form.name.trim()) {
      setError("Vendor name is required");
      return;
    }
    try {
      const payload = {
        ...form,
        email: form.email.trim() || null,
        phone: form.phone.trim() || null,
        address: form.address.trim() || null,
        contact_name: form.contact_name.trim() || null,
        tax_identifier: form.tax_identifier.trim() || null,
      };

      if (editingId) {
        await api.put(`/admin/vendors/${editingId}`, payload);
      } else {
        await api.post("/admin/vendors", payload);
      }
      setOpen(false);
      load();
    } catch (e) {
      setError(apiError(e));
    }
  };

  const toggleActive = async (item: Vendor) => {
    try {
      const payload = {
        name: item.name,
        contact_name: item.contact_name,
        email: item.email,
        phone: item.phone,
        address: item.address,
        tax_identifier: item.tax_identifier,
        is_active: !item.is_active,
      };
      await api.put(`/admin/vendors/${item.id}`, payload);
      load();
    } catch (e) {
      setError(apiError(e));
    }
  };

  // Filter
  const filtered = items.filter((item) => {
    const term = search.toLowerCase();
    return (
      item.name.toLowerCase().includes(term) ||
      (item.contact_name?.toLowerCase() || "").includes(term) ||
      (item.email?.toLowerCase() || "").includes(term)
    );
  });

  const pageCount = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  return (
    <>
      <PageHeader
        title="Vendor Suppliers"
        subtitle="Configure pantry stockists, billing details, and active procurement sources."
        actionLabel="Add Vendor"
        onAction={() => begin()}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }} onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      {/* Search Filter */}
      <Card sx={{ mb: 4 }}>
        <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
          <Box display="flex" gap={2}>
            <TextField
              size="small"
              placeholder="Search by vendor name, contact person, or email..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              sx={{ flex: 1 }}
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
          </Box>
        </CardContent>
      </Card>

      {/* Vendors Table */}
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Vendor Supplier</TableCell>
              <TableCell>Contact Person</TableCell>
              <TableCell>Email Address</TableCell>
              <TableCell>Phone Number</TableCell>
              <TableCell>Tax Identifier</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Edit</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginated.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 6, color: "text.secondary" }}>
                  No vendor suppliers match the query.
                </TableCell>
              </TableRow>
            ) : (
              paginated.map((item) => (
                <TableRow key={item.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={600}>
                      {item.name}
                    </Typography>
                    {item.address && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        display="block"
                        sx={{ maxWidth: 240 }}
                        noWrap
                      >
                        {item.address}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>{item.contact_name ?? "—"}</TableCell>
                  <TableCell>{item.email ?? "—"}</TableCell>
                  <TableCell>{item.phone ?? "—"}</TableCell>
                  <TableCell sx={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
                    {item.tax_identifier ?? "—"}
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Switch checked={item.is_active} onChange={() => toggleActive(item)} />
                      <Chip
                        size="small"
                        color={item.is_active ? "success" : "default"}
                        label={item.is_active ? "Procuring" : "Inactive"}
                        sx={{ fontWeight: "bold" }}
                      />
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <IconButton color="primary" onClick={() => begin(item)}>
                      <EditOutlined />
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

      {/* Editor Dialog */}
      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editingId ? "Edit Vendor Details" : "Add New Supplier Vendor"}</DialogTitle>
        <DialogContent dividers>
          <Box display="flex" flexDirection="column" gap={2.5} pt={1}>
            <TextField
              label="Vendor Company Name"
              placeholder="e.g. Faridi Impex Pvt. Ltd."
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
            <TextField
              label="Contact Person Name"
              placeholder="e.g. J. S. Faridi"
              value={form.contact_name}
              onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
            />
            <TextField
              label="Email Address"
              type="email"
              placeholder="e.g. sales@faridi.com"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
            <TextField
              label="Phone Number"
              placeholder="e.g. +91 98765 43210"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
            />
            <TextField
              label="Business Address"
              placeholder="e.g. Sector 5, Okhla Industrial Area..."
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
              multiline
              rows={2}
            />
            <TextField
              label="Tax Identifier / GSTIN"
              placeholder="e.g. 07AAAAA1111A1Z1"
              value={form.tax_identifier}
              onChange={(e) => setForm({ ...form, tax_identifier: e.target.value })}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                />
              }
              label="Active procurement supplier"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={save}>
            Save Vendor
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
