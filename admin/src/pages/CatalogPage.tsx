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
  Grid,
  IconButton,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { DeleteOutline, EditOutlined } from "@mui/icons-material";
import { api, apiError } from "../api";
import { PageHeader } from "../components/PageHeader";
import type { ApiResponse, Entity } from "../types";

type EntityType = "regions" | "categories" | "brands";

function EntitySection({ type, title }: { type: EntityType; title: string }) {
  const [items, setItems] = useState<Entity[]>([]);
  const [error, setError] = useState("");

  // Create / Edit Form State
  const [open, setOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<Entity | null>(null);
  const [name, setName] = useState("");
  const [isActive, setIsActive] = useState(true);

  // Extra attributes based on type
  const [subtitle, setSubtitle] = useState("");
  const [description, setDescription] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [logoUrl, setLogoUrl] = useState("");
  const [displayOrder, setDisplayOrder] = useState(0);

  const load = () => {
    api
      .get<ApiResponse<Entity[]>>(`/admin/${type}`)
      .then((r) => setItems(r.data.data))
      .catch((e) => setError(apiError(e)));
  };

  useEffect(load, [type]);

  const openForm = (item?: Entity) => {
    setError("");
    if (item) {
      setEditingItem(item);
      setName(item.name);
      setIsActive(item.is_active);
      setSubtitle("");
      setDescription("");
      setImageUrl("");
      setLogoUrl("");
      setDisplayOrder(0);
    } else {
      setEditingItem(null);
      setName("");
      setIsActive(true);
      setSubtitle("");
      setDescription("");
      setImageUrl("");
      setLogoUrl("");
      setDisplayOrder(0);
    }
    setOpen(true);
  };

  const save = async () => {
    setError("");
    if (name.length < 2) {
      setError("Name must be at least 2 characters");
      return;
    }
    try {
      const payload: Record<string, unknown> = {
        name,
        is_active: isActive,
      };

      if (type === "regions") {
        payload.subtitle = subtitle || null;
        payload.description = description || null;
        payload.image_url = imageUrl || null;
        payload.display_order = Number(displayOrder);
      } else if (type === "categories") {
        payload.description = description || null;
      } else if (type === "brands") {
        payload.logo_url = logoUrl || null;
      }

      if (editingItem) {
        await api.put(`/admin/${type}/${editingItem.id}`, payload);
      } else {
        await api.post(`/admin/${type}`, payload);
      }
      setOpen(false);
      load();
    } catch (e) {
      setError(apiError(e));
    }
  };

  const remove = async (id: number) => {
    if (!window.confirm(`Are you sure you want to deactivate this ${title.toLowerCase()}?`)) return;
    try {
      await api.delete(`/admin/${type}/${id}`);
      load();
    } catch (e) {
      setError(apiError(e));
    }
  };

  return (
    <Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <CardContent sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" fontWeight={800}>
            {title}
          </Typography>
          <Button variant="outlined" size="small" onClick={() => openForm()}>
            Add New
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }} onClose={() => setError("")}>
            {error}
          </Alert>
        )}

        <Box display="flex" flexDirection="column" gap={1.5} sx={{ mt: 1 }}>
          {items.length === 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 3 }}>
              No {title.toLowerCase()} yet. Add one above.
            </Typography>
          )}
          {items.map((item) => (
            <Box
              key={item.id}
              display="flex"
              justifyContent="space-between"
              alignItems="flex-start"
              sx={{
                p: 1.5,
                border: "1px solid rgba(0,0,0,0.06)",
                borderRadius: 2,
                bgcolor: item.is_active ? "background.paper" : "rgba(0,0,0,0.02)",
              }}
            >
              <Box flex={1} minWidth={0}>
                <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
                  <Typography
                    variant="body2"
                    fontWeight={600}
                    color={item.is_active ? "text.primary" : "text.secondary"}
                    sx={{ textDecoration: item.is_active ? "none" : "line-through" }}
                  >
                    {item.name}
                  </Typography>
                  <Chip
                    size="small"
                    label={`${item.product_count ?? 0} products`}
                    sx={{ height: 20, borderRadius: 1 }}
                  />
                  {!item.is_active && <Chip size="small" label="Inactive" sx={{ height: 18 }} />}
                </Box>
                {/* Show subtitle for regions */}
                {type === "regions" && item.subtitle && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.3 }}>
                    {item.subtitle}
                  </Typography>
                )}
              </Box>
              <Box flexShrink={0}>
                <IconButton size="small" color="primary" onClick={() => openForm(item)}>
                  <EditOutlined fontSize="small" />
                </IconButton>
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => remove(item.id)}
                  disabled={!item.is_active}
                >
                  <DeleteOutline fontSize="small" />
                </IconButton>
              </Box>
            </Box>
          ))}
        </Box>

        {/* Create / Edit Dialog */}
        <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="xs">
          <DialogTitle>{editingItem ? `Edit ${title}` : `Create ${title}`}</DialogTitle>
          <DialogContent dividers>
            <Box display="flex" flexDirection="column" gap={2} pt={1}>
              <TextField
                label="Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                fullWidth
              />

              {type === "regions" && (
                <>
                  <TextField
                    label="Subtitle"
                    placeholder="Short tagline shown under region name"
                    value={subtitle}
                    onChange={(e) => setSubtitle(e.target.value)}
                    fullWidth
                  />
                  <TextField
                    label="Description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    fullWidth
                    multiline
                    rows={2}
                  />
                  <TextField
                    label="Image URL"
                    value={imageUrl}
                    onChange={(e) => setImageUrl(e.target.value)}
                    fullWidth
                  />
                  <TextField
                    label="Display Order"
                    type="number"
                    value={displayOrder}
                    onChange={(e) => setDisplayOrder(Number(e.target.value))}
                    fullWidth
                  />
                </>
              )}

              {type === "categories" && (
                <TextField
                  label="Description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  fullWidth
                  multiline
                  rows={2}
                />
              )}

              {type === "brands" && (
                <TextField
                  label="Logo URL"
                  value={logoUrl}
                  onChange={(e) => setLogoUrl(e.target.value)}
                  fullWidth
                />
              )}

              <FormControlLabel
                control={
                  <Switch checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
                }
                label="Active classification"
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button variant="contained" onClick={save}>
              Save
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
}

export function CatalogPage() {
  return (
    <>
      <PageHeader
        title="Regions & Taxonomy Catalog"
        subtitle="Manage product region tags, categories, brands, and active display filters."
      />
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 4 }}>
          <EntitySection type="regions" title="Regions" />
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <EntitySection type="categories" title="Categories" />
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <EntitySection type="brands" title="Brands" />
        </Grid>
      </Grid>
    </>
  );
}
