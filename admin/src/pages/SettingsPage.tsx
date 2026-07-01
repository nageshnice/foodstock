import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  FormControlLabel,
  Grid,
  Switch,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { api, apiError } from "../api";
import { PageHeader } from "../components/PageHeader";
import type { ApiResponse, AppSettingsGroup, ContentPage } from "../types";

const SECRET_MASK = "••••••••";

function SettingsFields({
  group,
  values,
  onChange,
  onToggleEnabled,
}: {
  group: AppSettingsGroup;
  values: Record<number, string>;
  onChange: (id: number, value: string) => void;
  onToggleEnabled: (enabled: boolean) => void;
}) {
  return (
    <Box>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box>
          <Typography variant="h6" fontWeight={700}>
            {group.group === "email" ? "Email notifications" : "Push notifications"}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {group.group === "email"
              ? "SMTP keys for order and account emails."
              : "Firebase keys for mobile push alerts."}
          </Typography>
        </Box>
        <FormControlLabel
          control={
            <Switch
              checked={group.enabled}
              onChange={(e) => onToggleEnabled(e.target.checked)}
            />
          }
          label={group.enabled ? "Active" : "Inactive"}
        />
      </Box>

      <Grid container spacing={2}>
        {group.settings
          .filter((s) => !s.setting_key.endsWith("_enabled"))
          .map((setting) => (
            <Grid size={{ xs: 12, md: 6 }} key={setting.id}>
              <TextField
                fullWidth
                label={setting.label}
                helperText={setting.description || undefined}
                type={setting.is_secret ? "password" : setting.value_type === "number" ? "number" : "text"}
                value={values[setting.id] ?? setting.value ?? ""}
                onChange={(e) => onChange(setting.id, e.target.value)}
                disabled={!group.enabled && !setting.setting_key.endsWith("_enabled")}
                placeholder={setting.is_secret && setting.has_value ? "Leave blank to keep current" : undefined}
              />
            </Grid>
          ))}
      </Grid>
    </Box>
  );
}

function ContentEditor({
  page,
  onSave,
  saving,
}: {
  page: ContentPage;
  onSave: (payload: ContentPage) => Promise<void>;
  saving: boolean;
}) {
  const [title, setTitle] = useState(page.title);
  const [body, setBody] = useState(page.body);
  const [isActive, setIsActive] = useState(page.is_active);
  const [contactEmail, setContactEmail] = useState(page.contact_email ?? "");
  const [contactPhone, setContactPhone] = useState(page.contact_phone ?? "");
  const [contactAddress, setContactAddress] = useState(page.contact_address ?? "");
  const [supportHours, setSupportHours] = useState(page.support_hours ?? "");

  useEffect(() => {
    setTitle(page.title);
    setBody(page.body);
    setIsActive(page.is_active);
    setContactEmail(page.contact_email ?? "");
    setContactPhone(page.contact_phone ?? "");
    setContactAddress(page.contact_address ?? "");
    setSupportHours(page.support_hours ?? "");
  }, [page]);

  const isContact = page.slug === "contact-us";

  return (
    <Box>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Chip label={page.slug} size="small" variant="outlined" />
        <FormControlLabel
          control={<Switch checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />}
          label={isActive ? "Published" : "Draft"}
        />
      </Box>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12 }}>
          <TextField fullWidth label="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
        </Grid>
        <Grid size={{ xs: 12 }}>
          <TextField
            fullWidth
            multiline
            minRows={8}
            label="Content (HTML supported)"
            value={body}
            onChange={(e) => setBody(e.target.value)}
          />
        </Grid>
        {isContact && (
          <>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Contact email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Contact phone"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                multiline
                minRows={2}
                label="Address"
                value={contactAddress}
                onChange={(e) => setContactAddress(e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Support hours"
                value={supportHours}
                onChange={(e) => setSupportHours(e.target.value)}
                placeholder="Mon–Sat 9:00 AM – 6:00 PM IST"
              />
            </Grid>
          </>
        )}
        <Grid size={{ xs: 12 }}>
          <Button
            variant="contained"
            disabled={saving}
            onClick={() =>
              onSave({
                ...page,
                title,
                body,
                is_active: isActive,
                contact_email: contactEmail || null,
                contact_phone: contactPhone || null,
                contact_address: contactAddress || null,
                support_hours: supportHours || null,
              })
            }
          >
            Save {page.title}
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
}

export function SettingsPage() {
  const [tab, setTab] = useState(0);
  const [groups, setGroups] = useState<AppSettingsGroup[]>([]);
  const [pages, setPages] = useState<ContentPage[]>([]);
  const [values, setValues] = useState<Record<number, string>>({});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [settingsRes, pagesRes] = await Promise.all([
        api.get<ApiResponse<AppSettingsGroup[]>>("/admin/settings"),
        api.get<ApiResponse<ContentPage[]>>("/admin/content-pages"),
      ]);
      setGroups(settingsRes.data.data);
      setPages(pagesRes.data.data);
      const initial: Record<number, string> = {};
      for (const group of settingsRes.data.data) {
        for (const setting of group.settings) {
          initial[setting.id] = setting.value ?? "";
        }
      }
      setValues(initial);
      setError("");
    } catch (e) {
      setError(apiError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const saveIntegrationGroup = async (groupKey: "email" | "push") => {
    const group = groups.find((g) => g.group === groupKey);
    if (!group) return;
    setSaving(true);
    setSuccess("");
    setError("");
    try {
      const items = group.settings.map((setting) => {
        const raw = values[setting.id] ?? setting.value ?? "";
        const value =
          setting.is_secret && (raw === SECRET_MASK || raw === "") ? undefined : raw;
        if (setting.setting_key.endsWith("_enabled")) {
          return {
            id: setting.id,
            value: group.enabled ? "true" : "false",
            is_active: group.enabled,
          };
        }
        return value === undefined ? { id: setting.id } : { id: setting.id, value };
      });
      const res = await api.put<ApiResponse<AppSettingsGroup[]>>("/admin/settings", { items });
      setGroups(res.data.data);
      setSuccess(`${groupKey === "email" ? "Email" : "Push"} settings saved.`);
    } catch (e) {
      setError(apiError(e));
    } finally {
      setSaving(false);
    }
  };

  const toggleGroupEnabled = (groupKey: "email" | "push", enabled: boolean) => {
    setGroups((prev) =>
      prev.map((g) => (g.group === groupKey ? { ...g, enabled } : g)),
    );
    const group = groups.find((g) => g.group === groupKey);
    const enabledSetting = group?.settings.find((s) => s.setting_key.endsWith("_enabled"));
    if (enabledSetting) {
      setValues((prev) => ({ ...prev, [enabledSetting.id]: enabled ? "true" : "false" }));
    }
  };

  const saveContentPage = async (payload: ContentPage) => {
    setSaving(true);
    setSuccess("");
    setError("");
    try {
      await api.put(`/admin/content-pages/${payload.slug}`, {
        title: payload.title,
        body: payload.body,
        is_active: payload.is_active,
        contact_email: payload.contact_email,
        contact_phone: payload.contact_phone,
        contact_address: payload.contact_address,
        support_hours: payload.support_hours,
      });
      await load();
      setSuccess(`${payload.title} saved.`);
    } catch (e) {
      setError(apiError(e));
    } finally {
      setSaving(false);
    }
  };

  const emailGroup = groups.find((g) => g.group === "email");
  const pushGroup = groups.find((g) => g.group === "push");
  const termsPage = pages.find((p) => p.slug === "terms-and-conditions");
  const privacyPage = pages.find((p) => p.slug === "privacy-policy");
  const contactPage = pages.find((p) => p.slug === "contact-us");

  return (
    <Box>
      <PageHeader
        title="Settings"
        subtitle="Email & push notification keys, terms, privacy policy, and contact page."
      />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError("")}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess("")}>
          {success}
        </Alert>
      )}

      <Card>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" scrollButtons="auto">
          <Tab label="Email" />
          <Tab label="Push notifications" />
          <Tab label="Terms & Conditions" />
          <Tab label="Privacy Policy" />
          <Tab label="Contact Us" />
        </Tabs>
        <CardContent>
          {loading ? (
            <Typography color="text.secondary">Loading settings…</Typography>
          ) : (
            <>
              {tab === 0 && emailGroup && (
                <Box>
                  <SettingsFields
                    group={emailGroup}
                    values={values}
                    onChange={(id, value) => setValues((prev) => ({ ...prev, [id]: value }))}
                    onToggleEnabled={(enabled) => toggleGroupEnabled("email", enabled)}
                  />
                  <Button sx={{ mt: 3 }} variant="contained" disabled={saving} onClick={() => saveIntegrationGroup("email")}>
                    Save email settings
                  </Button>
                </Box>
              )}
              {tab === 1 && pushGroup && (
                <Box>
                  <SettingsFields
                    group={pushGroup}
                    values={values}
                    onChange={(id, value) => setValues((prev) => ({ ...prev, [id]: value }))}
                    onToggleEnabled={(enabled) => toggleGroupEnabled("push", enabled)}
                  />
                  <Button sx={{ mt: 3 }} variant="contained" disabled={saving} onClick={() => saveIntegrationGroup("push")}>
                    Save push settings
                  </Button>
                </Box>
              )}
              {tab === 2 && termsPage && (
                <ContentEditor page={termsPage} onSave={saveContentPage} saving={saving} />
              )}
              {tab === 3 && privacyPage && (
                <ContentEditor page={privacyPage} onSave={saveContentPage} saving={saving} />
              )}
              {tab === 4 && contactPage && (
                <ContentEditor page={contactPage} onSave={saveContentPage} saving={saving} />
              )}
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
