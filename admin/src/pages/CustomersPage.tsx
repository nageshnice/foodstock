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
  FormControl,
  FormControlLabel,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Pagination,
  Select,
  Switch,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  AdminPanelSettingsOutlined,
  DeleteOutline,
  GroupOutlined,
  ManageAccountsOutlined,
  PeopleOutlined,
  SearchOutlined,
  ShieldOutlined,
} from "@mui/icons-material";
import { api, apiError } from "../api";
import { PageHeader } from "../components/PageHeader";
import type { ApiResponse, User } from "../types";

const ROLES = [
  { value: "", label: "All Users", icon: <GroupOutlined />, color: "#1976d2" },
  { value: "customer", label: "Customers", icon: <PeopleOutlined />, color: "#2e7d32" },
  { value: "staff", label: "Staff", icon: <ManageAccountsOutlined />, color: "#ed6c02" },
  { value: "admin", label: "Admins", icon: <AdminPanelSettingsOutlined />, color: "#9c27b0" },
  { value: "super_admin", label: "Super Admins", icon: <ShieldOutlined />, color: "#d32f2f" },
];

const ASSIGNABLE_ROLES = ROLES.filter((r) => r.value);

interface UserForm {
  email: string;
  password: string;
  full_name: string;
  phone: string;
  role: string;
  is_active: boolean;
}

const emptyUserForm = (): UserForm => ({
  email: "",
  password: "",
  full_name: "",
  phone: "",
  role: "customer",
  is_active: true,
});

export function CustomersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState<UserForm>(emptyUserForm());
  const [saving, setSaving] = useState(false);

  const [search, setSearch] = useState("");
  const [roleTab, setRoleTab] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get<ApiResponse<User[]>>("/admin/customers");
      setUsers(r.data.data);
    } catch (e) {
      setError(apiError(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const update = async (user: User, values: Partial<User>) => {
    try {
      await api.patch(`/admin/customers/${user.id}`, {
        role: values.role ?? user.role,
        is_active: values.is_active !== undefined ? values.is_active : user.is_active,
      });
      load();
    } catch (e) {
      setError(apiError(e));
    }
  };

  const remove = async (user: User) => {
    const label = user.full_name || user.email;
    if (
      !window.confirm(
        `Delete user "${label}"?\n\nThis cannot be undone. Users with orders cannot be deleted — suspend them instead.`,
      )
    ) {
      return;
    }
    try {
      await api.delete(`/admin/customers/${user.id}`);
      load();
    } catch (e) {
      setError(apiError(e));
    }
  };

  const openCreate = () => {
    setForm(emptyUserForm());
    setDialogOpen(true);
  };

  const create = async () => {
    if (!form.email.trim() || form.password.length < 8) {
      setError("Email and password (min 8 characters) are required.");
      return;
    }
    setSaving(true);
    try {
      await api.post("/admin/customers", {
        email: form.email.trim(),
        password: form.password,
        full_name: form.full_name.trim() || null,
        phone: form.phone.trim() || null,
        role: form.role,
        is_active: form.is_active,
      });
      setDialogOpen(false);
      setForm(emptyUserForm());
      load();
    } catch (e) {
      setError(apiError(e));
    } finally {
      setSaving(false);
    }
  };

  const selectedRole = ROLES[roleTab].value;
  const filtered = users.filter((u) => {
    const term = search.toLowerCase();
    const nameStr = u.full_name?.toLowerCase() || "";
    const emailStr = u.email.toLowerCase();
    const phoneStr = u.phone?.toLowerCase() || "";
    const matchesSearch =
      nameStr.includes(term) || emailStr.includes(term) || phoneStr.includes(term);
    const matchesRole = !selectedRole || u.role === selectedRole;
    return matchesSearch && matchesRole;
  });

  const pageCount = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  const counts = Object.fromEntries(
    ROLES.filter((r) => r.value).map((r) => [r.value, users.filter((u) => u.role === r.value).length]),
  );

  return (
    <>
      <PageHeader
        title="Users Management"
        subtitle="View, filter, and manage all user accounts across roles."
        actionLabel="Add User"
        onAction={openCreate}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }} onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={2} mb={3}>
        {ROLES.filter((r) => r.value).map((role) => (
          <Grid size={{ xs: 6, sm: 3, lg: 2 }} key={role.value}>
            <Card
              sx={{
                borderTop: `3px solid ${role.color}`,
                borderRadius: 3,
                boxShadow: "0 1px 4px rgba(0,0,0,.06)",
              }}
            >
              <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                <Box display="flex" alignItems="center" gap={1.5}>
                  <Box sx={{ color: role.color }}>{role.icon}</Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {counts[role.value] ?? 0}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" fontWeight={600}>
                      {role.label}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Tabs & Search */}
      <Card sx={{ mb: 4, borderRadius: 3 }}>
        <CardContent sx={{ p: 0, "&:last-child": { pb: 0 } }}>
          <Tabs
            value={roleTab}
            onChange={(_, val) => {
              setRoleTab(val);
              setPage(1);
            }}
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              px: 2,
              "& .MuiTab-root": { minHeight: 56, fontWeight: 600 },
              "& .Mui-selected": { fontWeight: 800 },
            }}
          >
            {ROLES.map((role) => (
              <Tab
                key={role.value}
                label={
                  <Box display="flex" alignItems="center" gap={1}>
                    {role.icon}
                    <span>{role.label}</span>
                    {role.value && (
                      <Chip
                        label={counts[role.value] ?? 0}
                        size="small"
                        sx={{
                          height: 20,
                          minWidth: 20,
                          fontSize: "0.7rem",
                          fontWeight: 700,
                        }}
                      />
                    )}
                  </Box>
                }
              />
            ))}
          </Tabs>

          <Box px={2} pb={2}>
            <TextField
              size="small"
              placeholder="Search by name, email, or phone..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              fullWidth
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

      {/* Users Table */}
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>User</TableCell>
              <TableCell>Contact</TableCell>
              <TableCell>Orders</TableCell>
              <TableCell>Total Spent</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginated.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 6, color: "text.secondary" }}>
                  {loading ? "Loading..." : "No users match the selected filters."}
                </TableCell>
              </TableRow>
            ) : (
              paginated.map((user) => (
                <TableRow key={user.id} hover>
                  <TableCell sx={{ fontWeight: "bold" }}>
                    <Box display="flex" alignItems="center" gap={1.5}>
                      <Box
                        sx={{
                          width: 36,
                          height: 36,
                          borderRadius: "50%",
                          bgcolor: user.image_url
                            ? "transparent"
                            : (user.role === "super_admin" ? "#d32f2f"
                              : user.role === "admin" ? "#9c27b0"
                              : user.role === "staff" ? "#ed6c02"
                              : "#2e7d32"),
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: "#fff",
                          fontWeight: 700,
                          fontSize: "0.85rem",
                          flexShrink: 0,
                          overflow: "hidden",
                        }}
                      >
                        {user.image_url ? (
                          <Box
                            component="img"
                            src={user.image_url}
                            alt=""
                            sx={{ width: "100%", height: "100%", objectFit: "cover" }}
                          />
                        ) : (
                          (user.full_name?.[0] ?? user.email[0]).toUpperCase()
                        )}
                      </Box>
                      <Box>
                        {user.full_name ?? "Unspecified"}
                        <Typography variant="caption" color="text.secondary" display="block">
                          Joined{" "}
                          {user.created_at
                            ? new Date(user.created_at).toLocaleDateString("en-IN", {
                                day: "numeric",
                                month: "short",
                                year: "numeric",
                              })
                            : "—"}
                          {" · "}
                          {user.addresses_count ?? 0} address{(user.addresses_count ?? 0) !== 1 ? "es" : ""}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{user.email}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {user.phone ?? "No phone"}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography fontWeight={600}>{user.orders_count ?? 0}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography fontWeight={600}>
                      ₹
                      {Number(user.total_spent ?? 0).toLocaleString("en-IN", {
                        minimumFractionDigits: 2,
                      })}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.role.replace("_", " ").toUpperCase()}
                      size="small"
                      color={
                        user.role === "super_admin"
                          ? "error"
                          : user.role === "admin"
                            ? "secondary"
                            : user.role === "staff"
                              ? "warning"
                              : "success"
                      }
                      variant="outlined"
                      sx={{ fontWeight: 700, fontSize: "0.7rem" }}
                      onClick={() => {
                        const nextRole =
                          user.role === "customer"
                            ? "staff"
                            : user.role === "staff"
                              ? "admin"
                              : user.role === "admin"
                                ? "super_admin"
                                : "customer";
                        update(user, { role: nextRole });
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Switch
                        checked={Boolean(user.is_active)}
                        onChange={(e) => update(user, { is_active: e.target.checked })}
                        size="small"
                      />
                      <Typography
                        variant="caption"
                        fontWeight={600}
                        color={user.is_active ? "success.main" : "text.secondary"}
                      >
                        {user.is_active ? "Active" : "Suspended"}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip
                      title={
                        user.role === "super_admin"
                          ? "Super admin cannot be deleted"
                          : (user.orders_count ?? 0) > 0
                            ? "Cannot delete — user has orders"
                            : "Delete user"
                      }
                    >
                      <span>
                        <IconButton
                          size="small"
                          color="error"
                          disabled={
                            user.role === "super_admin" || (user.orders_count ?? 0) > 0
                          }
                          onClick={() => remove(user)}
                          aria-label={`Delete ${user.email}`}
                        >
                          <DeleteOutline fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
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
            shape="rounded"
          />
        </Box>
      )}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add User</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid size={12}>
              <TextField
                label="Email"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                fullWidth
                required
              />
            </Grid>
            <Grid size={12}>
              <TextField
                label="Password"
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                fullWidth
                required
                helperText="Minimum 8 characters"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label="Full name"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                fullWidth
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label="Phone"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                fullWidth
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Role</InputLabel>
                <Select
                  label="Role"
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                >
                  {ASSIGNABLE_ROLES.map((role) => (
                    <MenuItem key={role.value} value={role.value}>
                      {role.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={form.is_active}
                    onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  />
                }
                label={form.is_active ? "Active" : "Suspended"}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setDialogOpen(false)} disabled={saving}>
            Cancel
          </Button>
          <Button variant="contained" onClick={create} disabled={saving}>
            {saving ? "Creating..." : "Create User"}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
