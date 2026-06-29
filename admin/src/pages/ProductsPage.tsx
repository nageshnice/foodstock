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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import {
  DeleteOutline,
  EditOutlined,
  SearchOutlined,
  AddCircleOutline,
  RemoveCircleOutline,
} from "@mui/icons-material";
import { api, apiError } from "../api";
import { PageHeader } from "../components/PageHeader";
import type { ApiResponse, Product, Entity, Vendor } from "../types";

interface ProductVariantForm {
  size: string;
  mrp: string;
  price: string;
  stock_quantity: number;
  low_stock_threshold: number;
  is_active: boolean;
}

interface ProductForm {
  sku: string;
  name: string;
  description: string;
  image_url: string;
  tax_rate: string;
  is_active: boolean;
  region_id: number | "";
  category_id: number | "";
  brand_id: number | "";
  vendor_id: number | "";
  variants: ProductVariantForm[];
}

const emptyVariant: ProductVariantForm = {
  size: "",
  mrp: "0",
  price: "0",
  stock_quantity: 0,
  low_stock_threshold: 5,
  is_active: true,
};

const createEmptyProduct = (): ProductForm => ({
  sku: "",
  name: "",
  description: "",
  image_url: "",
  tax_rate: "5.00",
  is_active: false,
  region_id: "",
  category_id: "",
  brand_id: "",
  vendor_id: "",
  variants: [{ ...emptyVariant }],
});

export function ProductsPage() {
  const [items, setItems] = useState<Product[]>([]);
  const [regions, setRegions] = useState<Entity[]>([]);
  const [categories, setCategories] = useState<Entity[]>([]);
  const [formBrands, setFormBrands] = useState<Entity[]>([]);
  const [filterBrands, setFilterBrands] = useState<Entity[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  // Form State
  const [form, setForm] = useState<ProductForm>(createEmptyProduct());
  const [imageUploading, setImageUploading] = useState(false);
  const [skuTouched, setSkuTouched] = useState(false);

  // Search & Filter State
  const [search, setSearch] = useState("");
  const [filterRegion, setFilterRegion] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterBrand, setFilterBrand] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  // Pagination State
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const loadBrandsForRegion = async (regionId: number | "") => {
    if (!regionId) {
      return [];
    }
    const r = await api.get<ApiResponse<Entity[]>>(`/admin/brands?region_id=${regionId}`);
    return r.data.data;
  };

  const suggestSku = async (regionId: number | "", categoryId: number | "") => {
    if (editingId || skuTouched) return;
    if (!regionId || !categoryId) {
      setForm((f) => ({ ...f, sku: "" }));
      return;
    }
    try {
      const r = await api.get<ApiResponse<{ sku: string; prefix: string }>>(
        `/admin/products/suggest-sku?region_id=${regionId}&category_id=${categoryId}`,
      );
      setForm((f) => ({ ...f, sku: r.data.data.sku }));
    } catch (e) {
      console.error("Failed to suggest SKU", e);
    }
  };

  const loadLookups = async () => {
    try {
      const [rReg, rCat, rVend] = await Promise.all([
        api.get<ApiResponse<Entity[]>>("/admin/regions"),
        api.get<ApiResponse<Entity[]>>("/admin/categories"),
        api.get<ApiResponse<Vendor[]>>("/admin/vendors"),
      ]);
      setRegions(rReg.data.data);
      setCategories(rCat.data.data);
      setVendors(rVend.data.data);
    } catch (e) {
      console.error("Failed to load catalog lookups", e);
    }
  };

  const loadProducts = async () => {
    setLoading(true);
    try {
      const r = await api.get<ApiResponse<Product[]>>("/admin/products");
      setItems(r.data.data);
    } catch (e) {
      setError(apiError(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
    loadLookups();
  }, []);

  useEffect(() => {
    if (!filterRegion) {
      setFilterBrands([]);
      setFilterBrand("");
      return;
    }
    loadBrandsForRegion(Number(filterRegion))
      .then(setFilterBrands)
      .catch((e) => console.error("Failed to load filter brands", e));
  }, [filterRegion]);

  const begin = async (product?: Product) => {
    setError("");
    setSkuTouched(!!product);
    if (product) {
      setEditingId(product.id);
      const regionId = product.region_id ?? "";
      const nextForm: ProductForm = {
        sku: product.sku,
        name: product.name,
        description: product.description ?? "",
        image_url: product.image_url ?? "",
        tax_rate: product.tax_rate,
        is_active: product.is_active,
        region_id: regionId,
        category_id: product.category_id ?? "",
        brand_id: product.brand_id ?? "",
        vendor_id: product.vendor_id ?? "",
        variants: product.variants.map((v) => ({
          size: v.size,
          mrp: String(v.mrp ?? v.price),
          price: String(v.price),
          stock_quantity: v.stock_quantity,
          low_stock_threshold: v.low_stock_threshold,
          is_active: v.is_active,
        })),
      };
      setForm(nextForm);
      if (regionId) {
        try {
          setFormBrands(await loadBrandsForRegion(regionId));
        } catch (e) {
          console.error("Failed to load brands for region", e);
          setFormBrands([]);
        }
      } else {
        setFormBrands([]);
      }
    } else {
      setEditingId(null);
      setForm(createEmptyProduct());
      setFormBrands([]);
      setSkuTouched(false);
    }
    setOpen(true);
  };

  const uploadImage = async (file: File) => {
    setImageUploading(true);
    setError("");
    try {
      const body = new FormData();
      body.append("file", file);
      const r = await api.post<ApiResponse<{ image_url: string }>>(
        "/admin/products/upload-image",
        body,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      setForm((prev) => ({ ...prev, image_url: r.data.data.image_url }));
    } catch (e) {
      setError(apiError(e));
    } finally {
      setImageUploading(false);
    }
  };

  const imagePreviewSrc = (url: string) => {
    if (!url) return "";
    if (url.startsWith("http")) return url;
    return `${window.location.origin}${url}`;
  };

  const save = async () => {
    setError("");
    try {
      // Validate inputs
      if (!form.name.trim()) {
        setError("Product name is required");
        return;
      }
      if (form.variants.length === 0) {
        setError("At least one variant is required");
        return;
      }
      for (const v of form.variants) {
        if (!v.size.trim()) {
          setError("Variant size is required");
          return;
        }
      }

      if (!form.region_id) {
        setError("Region is required");
        return;
      }
      if (!form.category_id) {
        setError("Category is required");
        return;
      }
      if (!form.brand_id) {
        setError("Brand is required");
        return;
      }

      let sku = form.sku.trim();
      if (!sku && !editingId) {
        const suggested = await api.get<ApiResponse<{ sku: string }>>(
          `/admin/products/suggest-sku?region_id=${form.region_id}&category_id=${form.category_id}`,
        );
        sku = suggested.data.data.sku;
      }

      const payload = {
        ...form,
        sku: sku || null,
        tax_rate: Number(form.tax_rate),
        region_id: form.region_id || null,
        category_id: form.category_id || null,
        brand_id: form.brand_id || null,
        vendor_id: form.vendor_id || null,
        variants: form.variants.map((v) => ({
          ...v,
          mrp: Number(v.mrp),
          price: Number(v.price),
        })),
      };

      if (editingId) {
        await api.put(`/admin/products/${editingId}`, payload);
      } else {
        await api.post("/admin/products", payload);
      }
      setOpen(false);
      loadProducts();
    } catch (e) {
      setError(apiError(e));
    }
  };

  const deactivate = async (id: number) => {
    if (!window.confirm("Are you sure you want to deactivate this product?")) return;
    try {
      await api.delete(`/admin/products/${id}`);
      loadProducts();
    } catch (e) {
      setError(apiError(e));
    }
  };

  // Filtering Logic
  const filtered = items.filter((item) => {
    const matchesSearch =
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.sku.toLowerCase().includes(search.toLowerCase());
    const matchesRegion = !filterRegion || String(item.region_id) === filterRegion;
    const matchesCategory = !filterCategory || String(item.category_id) === filterCategory;
    const matchesBrand = !filterBrand || String(item.brand_id) === filterBrand;
    const matchesStatus =
      !filterStatus ||
      (filterStatus === "live" ? item.is_active : !item.is_active);
    return matchesSearch && matchesRegion && matchesCategory && matchesBrand && matchesStatus;
  });

  const pageCount = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  // Variant editing handlers
  const addVariant = () => {
    setForm((f) => ({
      ...f,
      variants: [...f.variants, { ...emptyVariant }],
    }));
  };

  const removeVariant = (index: number) => {
    if (form.variants.length === 1) return;
    setForm((f) => ({
      ...f,
      variants: f.variants.filter((_, i) => i !== index),
    }));
  };

  const updateVariant = <K extends keyof ProductVariantForm>(
    index: number,
    field: K,
    value: ProductVariantForm[K],
  ) => {
    setForm((f) => {
      const next = [...f.variants];
      next[index] = { ...next[index], [field]: value };
      return { ...f, variants: next };
    });
  };

  return (
    <>
      <PageHeader
        title="Products Catalog"
        subtitle="Manage pantry SKU parameters, variants, taxes and pricing."
        actionLabel="Add Product"
        onAction={() => begin()}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }} onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      {/* Filter Toolbar */}
      <Card sx={{ mb: 4 }}>
        <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
          <Box display="grid" gridTemplateColumns={{ xs: "1fr", sm: "1fr 1fr", md: "2fr 1fr 1fr 1fr 1fr" }} gap={2}>
            <TextField
              size="small"
              placeholder="Search by SKU or name..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
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

            <FormControl size="small" fullWidth>
              <InputLabel>Region</InputLabel>
              <Select
                label="Region"
                value={filterRegion}
                onChange={(e) => {
                  setFilterRegion(e.target.value);
                  setFilterBrand("");
                  setPage(1);
                }}
              >
                <MenuItem value="">All Regions</MenuItem>
                {regions.map((r) => (
                  <MenuItem key={r.id} value={String(r.id)}>
                    {r.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                label="Category"
                value={filterCategory}
                onChange={(e) => {
                  setFilterCategory(e.target.value);
                  setPage(1);
                }}
              >
                <MenuItem value="">All Categories</MenuItem>
                {categories.map((c) => (
                  <MenuItem key={c.id} value={String(c.id)}>
                    {c.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" fullWidth disabled={!filterRegion}>
              <InputLabel>Brand</InputLabel>
              <Select
                label="Brand"
                value={filterBrand}
                onChange={(e) => {
                  setFilterBrand(e.target.value);
                  setPage(1);
                }}
              >
                <MenuItem value="">All Brands</MenuItem>
                {filterBrands.map((b) => (
                  <MenuItem key={b.id} value={String(b.id)}>
                    {b.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                label="Status"
                value={filterStatus}
                onChange={(e) => {
                  setFilterStatus(e.target.value);
                  setPage(1);
                }}
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="live">Live</MenuItem>
                <MenuItem value="draft">Draft</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      {/* Products Table */}
      <TableContainer sx={{ mb: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>SKU</TableCell>
              <TableCell>Product Name</TableCell>
              <TableCell>Region / Brand</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Variants & Pricing</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginated.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 6, color: "text.secondary" }}>
                  No products match the selected filters.
                </TableCell>
              </TableRow>
            ) : (
              paginated.map((item) => {
                const regionName =
                  item.region_name ??
                  regions.find((r) => r.id === item.region_id)?.name ??
                  "Unassigned";
                const brandName =
                  item.brand_name ?? "Unassigned";
                const categoryName =
                  item.category_name ??
                  categories.find((c) => c.id === item.category_id)?.name ??
                  "Unassigned";
                return (
                  <TableRow key={item.id} hover>
                    <TableCell sx={{ fontWeight: "bold", fontFamily: "monospace" }}>
                      {item.sku}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>
                        {item.name}
                      </Typography>
                      {item.source_section && (
                        <Typography variant="caption" color="text.secondary">
                          Section: {item.source_section}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{regionName}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {brandName}
                      </Typography>
                    </TableCell>
                    <TableCell>{categoryName}</TableCell>
                    <TableCell>
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {item.variants.map((v) => (
                          <Chip
                            key={v.id}
                            size="small"
                            variant="outlined"
                            label={`${v.size} — ₹${Number(v.price).toFixed(2)}${Number(v.mrp ?? v.price) > Number(v.price) ? ` (MRP ₹${Number(v.mrp ?? v.price).toFixed(2)})` : ""}`}
                            sx={{ borderRadius: 1.5 }}
                          />
                        ))}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        color={item.is_active ? "success" : "default"}
                        label={item.is_active ? "Live" : "Draft"}
                        sx={{ fontWeight: "bold" }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <IconButton onClick={() => begin(item)} color="primary" size="small">
                        <EditOutlined fontSize="small" />
                      </IconButton>
                      <IconButton
                        onClick={() => deactivate(item.id)}
                        color="error"
                        size="small"
                        disabled={!item.is_active}
                      >
                        <DeleteOutline fontSize="small" />
                      </IconButton>
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

      {/* Editor Modal */}
      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>{editingId ? "Edit Product Parameters" : "Add New Catalog Product"}</DialogTitle>
        <DialogContent dividers>
          <Box display="flex" flexDirection="column" gap={3} pt={1}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  label="Product Name"
                  placeholder="e.g. Organic Matcha Powder"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </Grid>

              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  label="SKU Code"
                  placeholder="Select region and category to auto-generate"
                  value={form.sku}
                  helperText={
                    editingId
                      ? "SKU stays fixed when editing unless you change it manually"
                      : "Auto-generated from region + category (e.g. exo-cur-003)"
                  }
                  onChange={(e) => {
                    setSkuTouched(true);
                    setForm({ ...form, sku: e.target.value });
                  }}
                />
              </Grid>

              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Region Classification</InputLabel>
                  <Select
                    label="Region Classification"
                    value={form.region_id}
                    onChange={async (e) => {
                      const raw = String(e.target.value);
                      const regionId = raw === "" ? "" : Number(raw);
                      const categoryId = form.category_id;
                      setForm({ ...form, region_id: regionId, brand_id: "" });
                      if (regionId) {
                        try {
                          setFormBrands(await loadBrandsForRegion(regionId));
                        } catch (err) {
                          console.error("Failed to load brands for region", err);
                          setFormBrands([]);
                        }
                      } else {
                        setFormBrands([]);
                      }
                      await suggestSku(regionId, categoryId);
                    }}
                  >
                    <MenuItem value="">Select region</MenuItem>
                    {regions.map((r) => (
                      <MenuItem key={r.id} value={r.id}>
                        {r.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth disabled={!form.region_id}>
                  <InputLabel>Brand Name</InputLabel>
                  <Select
                    label="Brand Name"
                    value={form.brand_id}
                    onChange={(e) => setForm({ ...form, brand_id: e.target.value })}
                  >
                    <MenuItem value="">
                      {form.region_id ? "Select brand" : "Select a region first"}
                    </MenuItem>
                    {formBrands.map((b) => (
                      <MenuItem key={b.id} value={b.id}>
                        {b.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Category</InputLabel>
                  <Select
                    label="Category"
                    value={form.category_id}
                    onChange={async (e) => {
                      const raw = String(e.target.value);
                      const categoryId = raw === "" ? "" : Number(raw);
                      setForm({ ...form, category_id: categoryId });
                      await suggestSku(form.region_id, categoryId);
                    }}
                  >
                    <MenuItem value="">Select category</MenuItem>
                    {categories.map((c) => (
                      <MenuItem key={c.id} value={c.id}>
                        {c.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Primary Vendor</InputLabel>
                  <Select
                    label="Primary Vendor"
                    value={form.vendor_id}
                    onChange={(e) => setForm({ ...form, vendor_id: e.target.value })}
                  >
                    <MenuItem value="">No Supplier</MenuItem>
                    {vendors.map((v) => (
                      <MenuItem key={v.id} value={v.id}>
                        {v.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  label="GST Tax Rate %"
                  type="number"
                  value={form.tax_rate}
                  onChange={(e) => setForm({ ...form, tax_rate: e.target.value })}
                />
              </Grid>

              <Grid size={{ xs: 12 }}>
                <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                  Product Image
                </Typography>
                <Box display="flex" gap={2} alignItems="flex-start" flexWrap="wrap">
                  {form.image_url ? (
                    <Box
                      component="img"
                      src={imagePreviewSrc(form.image_url)}
                      alt="Product preview"
                      sx={{
                        width: 96,
                        height: 96,
                        objectFit: "cover",
                        borderRadius: 2,
                        border: "1px solid",
                        borderColor: "divider",
                      }}
                    />
                  ) : null}
                  <Box display="grid" gap={1.5} flex={1} minWidth={220}>
                    <Button variant="outlined" component="label" disabled={imageUploading}>
                      {imageUploading ? "Uploading..." : "Upload image file"}
                      <input
                        type="file"
                        hidden
                        accept="image/jpeg,image/png,image/webp,image/gif"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) void uploadImage(file);
                          e.target.value = "";
                        }}
                      />
                    </Button>
                    <TextField
                      fullWidth
                      size="small"
                      label="Or paste image URL"
                      value={form.image_url}
                      onChange={(e) => setForm({ ...form, image_url: e.target.value })}
                    />
                  </Box>
                </Box>
              </Grid>

              <Grid size={{ xs: 12 }}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Product Description"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </Grid>

              <Grid size={{ xs: 12 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={form.is_active}
                      onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                    />
                  }
                  label="Product is live in catalog"
                />
              </Grid>
            </Grid>

            {/* Multiple Variants Block */}
            <Box>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="h6" fontWeight={700}>
                  Product Variants
                </Typography>
                <Button
                  size="small"
                  startIcon={<AddCircleOutline />}
                  onClick={addVariant}
                  variant="outlined"
                >
                  Add Variant
                </Button>
              </Box>

              <Box display="flex" flexDirection="column" gap={2}>
                {form.variants.map((v, i) => (
                  <Box
                    key={i}
                    display="flex"
                    gap={2}
                    alignItems="center"
                    sx={{
                      p: 2,
                      border: "1px dashed rgba(0,0,0,0.12)",
                      borderRadius: 2,
                      bgcolor: "rgba(0,0,0,0.01)",
                    }}
                  >
                    <TextField
                      size="small"
                      label="Size (e.g. 500 Gm, 1 Kg)"
                      value={v.size}
                      onChange={(e) => updateVariant(i, "size", e.target.value)}
                      required
                      sx={{ flex: 2 }}
                    />
                    <TextField
                      size="small"
                      label="MRP ₹"
                      type="number"
                      value={v.mrp}
                      onChange={(e) => updateVariant(i, "mrp", e.target.value)}
                      required
                      sx={{ flex: 1 }}
                    />
                    <TextField
                      size="small"
                      label="Offer Price ₹"
                      type="number"
                      value={v.price}
                      onChange={(e) => updateVariant(i, "price", e.target.value)}
                      required
                      sx={{ flex: 1 }}
                    />
                    <TextField
                      size="small"
                      label="Opening Stock"
                      type="number"
                      value={v.stock_quantity}
                      onChange={(e) => updateVariant(i, "stock_quantity", Number(e.target.value))}
                      required
                      sx={{ flex: 1 }}
                    />
                    <TextField
                      size="small"
                      label="Low Warning"
                      type="number"
                      value={v.low_stock_threshold}
                      onChange={(e) =>
                        updateVariant(i, "low_stock_threshold", Number(e.target.value))
                      }
                      required
                      sx={{ flex: 1 }}
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={v.is_active}
                          onChange={(e) => updateVariant(i, "is_active", e.target.checked)}
                          size="small"
                        />
                      }
                      label="Active"
                    />
                    <IconButton
                      color="error"
                      onClick={() => removeVariant(i)}
                      disabled={form.variants.length === 1}
                    >
                      <RemoveCircleOutline />
                    </IconButton>
                  </Box>
                ))}
              </Box>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={save}>
            Save Product
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
